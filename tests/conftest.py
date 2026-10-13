import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.pipeline.orchestrator import Orchestrator
from app.providers import MockProvider

MOCK = Path(__file__).resolve().parent.parent / "mock_data"
SCENARIOS = sorted((MOCK / "scenarios").glob("[0-9]*.json"))


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.fixture
def catalog():
    return load(MOCK / "catalog.json")


@pytest.fixture
def base_request(catalog):
    return {"business": {}, "customer": {}, "conversation": [], "catalog": catalog, "businessKnowledge": {}, "message": "x"}


@pytest.fixture
def settings():
    return Settings(provider="mock", ai_service_key="", mock_data_dir=MOCK)


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings=settings))


class FakeProvider:
    """Returns whatever we hand it - used to simulate a misbehaving LLM."""
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls, self.last_request = result, error, 0, None

    async def generate(self, request):
        self.calls += 1
        self.last_request = request
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def orchestrator(settings):
    return Orchestrator(MockProvider(settings.mock_data_dir))
