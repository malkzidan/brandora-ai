import pytest

from app.pipeline.orchestrator import SAFE_FALLBACK, Orchestrator
from app.providers import ProviderError
from app.schemas import AiRequest
from tests.conftest import FakeProvider

REQ = AiRequest.model_validate({"message": "سلام"})


async def test_provider_error_gives_safe_reply():
    out = await Orchestrator(FakeProvider(error=ProviderError("503"))).handle(REQ)
    assert out == SAFE_FALLBACK and out.intent.value == "UNKNOWN"


@pytest.mark.parametrize("bad", [{"intent": "NOPE"}, "not json", None,
                                 {"intent": "GREETING", "reply": "تم تأكيد طلبك", "productReference": None,
                                  "requiresReview": False, "orderCandidate": None}])
async def test_invalid_provider_output_gives_safe_reply(bad):
    out = await Orchestrator(FakeProvider(result=bad)).handle(REQ)
    assert out == SAFE_FALLBACK


async def test_fallback_is_a_copy_not_shared_state():
    out = await Orchestrator(FakeProvider(error=ProviderError("x"))).handle(REQ)
    out.reply = "changed"
    assert SAFE_FALLBACK.reply != "changed"
