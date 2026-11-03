"""Environment-driven settings. Nothing secret is ever logged or echoed back."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Router = small/fast model (classification + entity extraction, strict JSON).
DEFAULT_ROUTER_MODELS = ("gemini-flash-lite-latest", "gemini-2.5-flash-lite")
# Generator = larger model that phrases the final reply from verified facts.
DEFAULT_GENERATOR_MODELS = ("gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash")


class ConfigError(RuntimeError):
    """Invalid configuration; the service refuses to start (fail fast)."""


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _num(name: str, default: float) -> float:
    raw = os.getenv(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except ValueError:
        return default


def _models(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(m.strip() for m in raw.split(",") if m.strip()) or default


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "gemini"                  # "gemini" (production) | "rules" (deterministic, offline, no key)
    gemini_api_key: str | None = None
    router_models: tuple[str, ...] = DEFAULT_ROUTER_MODELS
    generator_models: tuple[str, ...] = DEFAULT_GENERATOR_MODELS
    generator_enabled: bool = True               # false = Router only, replies come straight from the verified templates
    router_temperature: float = 0.0
    generator_temperature: float = 0.3
    gemini_timeout_seconds: float = 12.0         # per call
    gemini_total_timeout_seconds: float = 25.0   # per stage (router / generator), so WhatsApp never waits forever
    gemini_max_retries: int = 2                  # per model, for transient (network/timeout/bad-JSON) errors
    gemini_retry_delay_seconds: float = 3.0
    gemini_cooldown_seconds: float = 60.0        # a model that returned 503/429 is skipped for this long
    ai_service_token: str | None = None          # shared secret the backend sends in X-Internal-Token
    enable_dev_endpoints: bool = False           # /v1/dev/* (mock data playground). Never enable in production.
    fallback_to_rules: bool = True               # Router failed on every model: True = rule router, False = HTTP 503
    min_confidence: float = 0.4
    log_level: str = "INFO"

    @property
    def llm_enabled(self) -> bool:
        return self.ai_provider == "gemini"

    def validate(self) -> "Settings":
        if self.ai_provider not in {"gemini", "rules"}:
            raise ConfigError(f"AI_PROVIDER must be 'gemini' or 'rules' (got {self.ai_provider!r})")
        if self.ai_provider == "gemini" and not self.gemini_api_key:
            raise ConfigError("AI_PROVIDER=gemini requires GEMINI_API_KEY (or set AI_PROVIDER=rules for the offline engine)")
        return self


def load_settings() -> Settings:
    return Settings(
        ai_provider=(os.getenv("AI_PROVIDER") or "gemini").strip().lower(),
        gemini_api_key=(os.getenv("GEMINI_API_KEY") or "").strip() or None,
        router_models=_models("ROUTER_MODELS", DEFAULT_ROUTER_MODELS),
        generator_models=_models("GENERATOR_MODELS", DEFAULT_GENERATOR_MODELS),
        generator_enabled=_bool("GENERATOR_ENABLED", True),
        router_temperature=_num("ROUTER_TEMPERATURE", 0.0),
        generator_temperature=_num("GENERATOR_TEMPERATURE", 0.3),
        gemini_timeout_seconds=_num("GEMINI_TIMEOUT_SECONDS", 12.0),
        gemini_total_timeout_seconds=_num("GEMINI_TOTAL_TIMEOUT_SECONDS", 25.0),
        gemini_max_retries=int(_num("GEMINI_MAX_RETRIES", 2)),
        gemini_retry_delay_seconds=_num("GEMINI_RETRY_DELAY_SECONDS", 3.0),
        gemini_cooldown_seconds=_num("GEMINI_COOLDOWN_SECONDS", 60.0),
        ai_service_token=(os.getenv("AI_SERVICE_TOKEN") or "").strip() or None,
        enable_dev_endpoints=_bool("ENABLE_DEV_ENDPOINTS", False),
        fallback_to_rules=_bool("AI_FALLBACK_TO_RULES", True),
        min_confidence=_num("MIN_CONFIDENCE", 0.4),
        log_level=(os.getenv("LOG_LEVEL") or "INFO").upper(),
    )
