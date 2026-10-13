from app.config import Settings

from .base import Provider, ProviderError
from .mock import MockProvider


def build_provider(settings: Settings) -> Provider:
    if settings.provider == "mock":
        return MockProvider(settings.mock_data_dir)
    raise ValueError(f"Unknown AI_PROVIDER '{settings.provider}'. Available now: mock (gemini arrives in F9).")


__all__ = ["Provider", "ProviderError", "MockProvider", "build_provider"]
