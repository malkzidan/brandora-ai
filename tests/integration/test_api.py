import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import MOCK


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "mock"}


def test_respond_happy_path(client, base_request):
    body = {**base_request, "message": "الهودي بكام؟"}
    r = client.post("/v1/ai/respond", json=body)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"intent", "reply", "productReference", "requiresReview", "orderCandidate"}
    assert data["intent"] == "INQUIRY_PRICE" and "520" in data["reply"]


def test_unknown_message_gets_unknown_intent(client, base_request):
    r = client.post("/v1/ai/respond", json={**base_request, "message": "asdfgh"})
    assert r.status_code == 200 and r.json()["intent"] == "UNKNOWN"


@pytest.mark.parametrize("bad", [{}, {"catalog": []}, {"message": 5}, {"message": "x", "catalog": [{"name": "no id"}]}])
def test_bad_request_uses_error_envelope(client, bad):
    r = client.post("/v1/ai/respond", json=bad)
    body = r.json()
    assert r.status_code == 400 and body["code"] == "VALIDATION_ERROR" and body["statusCode"] == 400


def test_extra_request_fields_are_tolerated(client, base_request):
    r = client.post("/v1/ai/respond", json={**base_request, "message": "الهودي بكام؟", "somethingNew": 1})
    assert r.status_code == 200


def test_service_key_enforced_when_configured(base_request):
    c = TestClient(create_app(settings=Settings(provider="mock", ai_service_key="secret", mock_data_dir=MOCK)))
    body = {**base_request, "message": "الهودي بكام؟"}
    assert c.post("/v1/ai/respond", json=body).status_code == 401
    assert c.post("/v1/ai/respond", json=body, headers={"X-AI-Service-Key": "wrong"}).status_code == 401
    assert c.post("/v1/ai/respond", json=body, headers={"X-AI-Service-Key": "secret"}).status_code == 200


def test_swagger_available(client):
    assert client.get("/docs").status_code == 200


def test_unknown_provider_fails_fast():
    from app.providers import build_provider
    with pytest.raises(ValueError):
        build_provider(Settings(provider="gemini", ai_service_key="", mock_data_dir=MOCK))
