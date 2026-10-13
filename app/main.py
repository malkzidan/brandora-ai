"""HTTP layer. NestJS calls POST /v1/ai/respond; Swagger UI is at /docs (this is the "manual testing" tool)."""
import hmac
import math

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings, load_settings
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.throttle import SlidingWindowThrottle, Throttled
from app.providers import build_provider
from app.schemas import AiRequest, AiResponse


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _envelope(status: int, code: str, message: str, error: str) -> JSONResponse:
    # Same error shape the NestJS backend uses, so both services "speak" the same way.
    return JSONResponse(status_code=status, content={"statusCode": status, "code": code, "message": message, "error": error})


def create_app(orchestrator: Orchestrator | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    orchestrator = orchestrator or Orchestrator(
        build_provider(settings),
        SlidingWindowThrottle(settings.throttle_max_messages, settings.throttle_window_seconds),
    )
    app = FastAPI(title="Brandora AI Service", version="0.1.0")

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _envelope(exc.status, exc.code, exc.message, "Unauthorized" if exc.status == 401 else "Error")

    @app.exception_handler(Throttled)
    async def _throttled(_: Request, exc: Throttled):
        wait = max(1, math.ceil(exc.retry_after))
        resp = _envelope(429, "AI_RATE_LIMITED", f"Too many messages from this customer. Retry in {wait}s.", "Too Many Requests")
        resp.headers["Retry-After"] = str(wait)
        return resp

    @app.exception_handler(RequestValidationError)
    async def _bad_request(_: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"] if p != "body")
        return _envelope(400, "VALIDATION_ERROR", f"{where}: {first['msg']}", "Bad Request")

    @app.get("/health")
    async def health():
        return {"status": "ok", "provider": settings.provider}

    @app.post("/v1/ai/respond", response_model=AiResponse)
    async def respond(body: AiRequest, x_ai_service_key: str | None = Header(default=None)):
        if settings.ai_service_key and not hmac.compare_digest(x_ai_service_key or "", settings.ai_service_key):
            raise AppError(401, "AI_UNAUTHORIZED", "Missing or invalid X-AI-Service-Key")
        return await orchestrator.handle(body)

    return app


app = create_app()
