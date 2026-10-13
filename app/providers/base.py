"""A provider = "the thing that produces the raw answer". Mock now, Gemini in F9, Ollama optionally.
The rest of the app only knows this interface, so swapping providers never touches the pipeline."""
from typing import Any, Protocol

from app.schemas import AiRequest


class ProviderError(Exception):
    """Provider failed (timeout, quota, network...). Orchestrator answers with the safe fallback."""


class Provider(Protocol):
    async def generate(self, request: AiRequest) -> dict[str, Any]:
        """Return the RAW response dict (same shape as the contract). It is validated afterwards."""
        ...
