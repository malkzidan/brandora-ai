"""The conductor. Order of work for every message:
   throttle -> clean -> empty? -> hard-coded rule? -> provider (LLM) -> guard -> (safe fallback if anything breaks)
Later features plug in here: F2.. add steps after the rules, F8 adds logging."""
import logging

from app.pipeline.preprocess import clean_message
from app.pipeline.rules import empty_response, match_rule
from app.pipeline.throttle import SlidingWindowThrottle, Throttled, throttle_key
from app.providers import Provider, ProviderError
from app.schemas import AiRequest, AiResponse, Intent
from app.validation.output_guard import OutputRejected, validate_output

log = logging.getLogger("brandora.ai")

SAFE_FALLBACK = AiResponse(
    intent=Intent.UNKNOWN,
    reply="معلش، في مشكلة تقنية بسيطة. ممكن تجرب تاني؟",
    productReference=None,
    requiresReview=False,
    orderCandidate=None,
)


class Orchestrator:
    def __init__(self, provider: Provider, throttle: SlidingWindowThrottle | None = None):
        self._provider = provider
        self._throttle = throttle

    async def handle(self, request: AiRequest) -> AiResponse:
        if self._throttle:
            key = throttle_key(request.business, request.customer)
            if key and (retry_after := self._throttle.hit(key)) is not None:
                raise Throttled(retry_after)

        cleaned = clean_message(request.message)
        if not cleaned:
            return empty_response()
        if (ruled := match_rule(cleaned)) is not None:
            return ruled

        request = request.model_copy(update={"message": cleaned})   # downstream only ever sees the clean text
        try:
            raw = await self._provider.generate(request)
            return validate_output(raw, request)
        except (ProviderError, OutputRejected) as exc:
            log.warning("fallback used: %s", exc)
            return SAFE_FALLBACK.model_copy(deep=True)
