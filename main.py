"""Brandora AI Service - FastAPI entry point.

Run:   uvicorn main:app --port 8000          Docs: http://localhost:8000/docs
Needs: AI_PROVIDER=gemini + GEMINI_API_KEY   (or AI_PROVIDER=rules to run the deterministic engine without a key)
"""
from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, load_settings
from app.pipeline.orchestrator import AIUnavailable, Orchestrator
from app.providers import Providers, build_providers
from app.schemas import AIRespondRequest, AiResponse

logger = logging.getLogger("brandora")


def create_app(settings: Settings | None = None, providers: Providers | None = None) -> FastAPI:
    settings = (settings or load_settings()).validate()      # fail fast on a bad/missing configuration
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "google_genai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)   # keep request details (and anything key-like) out of logs

    providers = providers or build_providers(settings)
    orchestrator = Orchestrator(settings, providers)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # No model calls at startup: Gemini is initialised lazily on the first request.
        logger.info("Brandora AI Service | provider=%s | router=%s | generator=%s | dev_endpoints=%s | auth=%s",
                    providers.name, ",".join(settings.router_models) if providers.name == "gemini" else "-",
                    "on" if providers.generator else "off", settings.enable_dev_endpoints,
                    "token" if settings.ai_service_token else "none")
        if not settings.ai_service_token:
            logger.warning("AI_SERVICE_TOKEN is not set: the endpoints are open. Set it before exposing the service.")
        if settings.enable_dev_endpoints:
            logger.warning("ENABLE_DEV_ENDPOINTS=true: mock-data playground is exposed. Never do this in production.")
            
        # Proactive Health Check on Startup
        if providers.name == "gemini" and providers.probe:
            logger.info("Running startup probe to verify active models...")
            try:
                probe_results = await providers.probe()
                logger.info("Startup Probe Results: %s", probe_results)
            except Exception as e:
                logger.error("Startup probe failed to execute: %s", e)
                
        yield

    app = FastAPI(title="Brandora AI Service", version="2.0.0", lifespan=lifespan,
                  description="Router + Generator over Gemini. Contract: E0-3 Structured Order Candidate, Schema 1.0.")
    app.state.orchestrator, app.state.settings, app.state.providers = orchestrator, settings, providers

    def require_token(x_internal_token: str | None = Header(default=None)) -> None:
        expected = settings.ai_service_token
        if expected and not (x_internal_token and hmac.compare_digest(x_internal_token, expected)):
            raise HTTPException(status_code=401, detail="invalid or missing X-Internal-Token")

    # ----------------------------------------------------------------- errors

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"),
                    "message": str(e["msg"]).removeprefix("Value error, ")} for e in exc.errors()]
        return JSONResponse(status_code=400, content={"error": "VALIDATION_ERROR", "details": details})

    @app.exception_handler(AIUnavailable)
    async def _ai_down(_: Request, exc: AIUnavailable):
        return JSONResponse(status_code=503, headers={"Retry-After": "10"},
                            content={"error": "AI_UNAVAILABLE", "message": "all AI models are busy, retry shortly"})

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        logger.exception("unhandled error")   # the stack trace stays in our logs, never in the response
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR"})

    # ----------------------------------------------------------------- routes

    @app.get("/", tags=["health"])
    async def root() -> dict[str, Any]:
        return {"service": "brandora-ai", "status": "ok", "docs": "/docs"}

    @app.get("/health", tags=["health"])
    async def health(probe: bool = Query(False, description="make one tiny live call per model role")) -> dict[str, Any]:
        out: dict[str, Any] = {"status": "ok", "ai": providers.health(), "fallbackToRules": settings.fallback_to_rules,
                               "devEndpoints": settings.enable_dev_endpoints}
        if probe and providers.probe:
            out["ai"]["probe"] = await providers.probe()
        return out

    @app.post("/v1/ai/respond", response_model=AiResponse, tags=["ai"], dependencies=[Depends(require_token)])
    async def respond(request: AIRespondRequest, response: Response) -> AiResponse:
        logger.info("[RECV] customer=%s message=%s chars=%d catalog=%d", request.customer.id, request.messageId,
                    len(request.text), len(request.catalog))
        logger.debug("message text: %s", request.text)   # customer content only at DEBUG
        result, trace = await orchestrator.respond(request)
        # Observability goes in headers, so the body stays EXACTLY the E0-3 schema (additionalProperties:false).
        response.headers["X-AI-Source"] = trace.router_source
        response.headers["X-AI-Detailed-Intent"] = trace.detailed_intent
        response.headers["X-AI-Latency-Ms"] = str(trace.latency_ms)
        if trace.router_model:
            response.headers["X-AI-Router-Model"] = trace.router_model
        if trace.generator_model:
            response.headers["X-AI-Generator-Model"] = trace.generator_model
        if trace.guard_violations:
            response.headers["X-AI-Guard"] = "fallback-to-template"
        return result

    if settings.enable_dev_endpoints:
        from app.dev import build_dev_router

        app.include_router(build_dev_router(orchestrator, require_token), prefix="/v1/dev", tags=["dev"])

    return app


app = create_app()