import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.pipeline.orchestrator import Orchestrator
from app.pipeline.throttle import SlidingWindowThrottle, Throttled
from app.schemas import AiRequest
from tests.conftest import MOCK, SCENARIOS, FakeProvider, load

RULE_SCENARIOS = [p for p in SCENARIOS if load(p)["handledBy"] == "rules"]


def req(message, **extra):
    return AiRequest.model_validate({"message": message, **extra})


@pytest.mark.parametrize("path", RULE_SCENARIOS, ids=lambda p: p.stem)
async def test_rule_scenarios_never_touch_the_llm(path):
    provider = FakeProvider(error=AssertionError("LLM must not be called"))
    out = await Orchestrator(provider).handle(AiRequest.model_validate(load(path)["request"]))
    assert out.model_dump(mode="json") == load(path)["expectedResponse"] and provider.calls == 0


@pytest.mark.parametrize("msg", ["", "   ", "🙂🙂", "\u200b\u200b"])
async def test_empty_messages_are_answered_without_llm(msg):
    provider = FakeProvider(error=AssertionError("LLM must not be called"))
    out = await Orchestrator(provider).handle(req(msg))
    assert out.intent.value == "UNKNOWN" and out.reply == "معلش، ممكن توضح طلبك؟" and provider.calls == 0


async def test_provider_receives_the_cleaned_message():
    provider = FakeProvider(result={"intent": "UNKNOWN", "reply": "؟", "productReference": None,
                                    "requiresReview": False, "orderCandidate": None})
    await Orchestrator(provider).handle(req("  عايزززز   تيشيرت 😍  ٣ قطع "))
    assert provider.calls == 1 and provider.last_request.message == "عايز تيشيرت 3 قطع"


async def test_mixed_greeting_and_request_goes_to_llm():
    provider = FakeProvider(result={"intent": "INQUIRY_PRICE", "reply": "وعليكم السلام، 520 جنيه", "productReference": None,
                                    "requiresReview": False, "orderCandidate": None})
    out = await Orchestrator(provider).handle(req("السلام عليكم الهودي بكام؟"))
    assert provider.calls == 1 and out.intent.value == "INQUIRY_PRICE"


async def test_throttle_blocks_after_limit_per_customer():
    orch = Orchestrator(FakeProvider(error=AssertionError("unused")), SlidingWindowThrottle(2, 60))
    body = dict(business={"id": "b"}, customer={"id": "c1"})
    await orch.handle(req("اهلا", **body)); await orch.handle(req("اهلا", **body))
    with pytest.raises(Throttled):
        await orch.handle(req("اهلا", **body))
    await orch.handle(req("اهلا", business={"id": "b"}, customer={"id": "c2"}))      # other customer unaffected
    for _ in range(5):                                                               # no customer id -> not throttled
        await orch.handle(req("اهلا"))


def api(max_messages=2):
    return TestClient(create_app(settings=Settings("mock", "", MOCK, max_messages, 60.0)))


def test_api_greeting_with_emoji_gets_fixed_reply(client):
    r = client.post("/v1/ai/respond", json={"message": "السلام عليكم 🌹🌹"})
    assert r.status_code == 200
    assert r.json()["reply"] == "وعليكم السلام ورحمة الله وبركاته! أهلاً بحضرتك، إزاي أقدر أساعدك؟"


def test_api_returns_429_with_retry_after():
    c = api(2)
    body = {"message": "اهلا", "business": {"id": "b"}, "customer": {"id": "c1"}}
    assert c.post("/v1/ai/respond", json=body).status_code == 200
    assert c.post("/v1/ai/respond", json=body).status_code == 200
    r = c.post("/v1/ai/respond", json=body)
    assert r.status_code == 429
    assert r.json()["code"] == "AI_RATE_LIMITED" and r.json()["statusCode"] == 429
    assert 1 <= int(r.headers["Retry-After"]) <= 60
    other = {**body, "customer": {"id": "c2"}}
    assert c.post("/v1/ai/respond", json=other).status_code == 200
