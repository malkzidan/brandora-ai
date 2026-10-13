"""Golden test: every scenario in mock_data must travel request -> orchestrator -> guard and come out identical."""
import pytest

from app.schemas import AiRequest
from tests.conftest import SCENARIOS, load


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
async def test_scenario_roundtrip(path, orchestrator):
    data = load(path)
    response = await orchestrator.handle(AiRequest.model_validate(data["request"]))
    assert response.model_dump(mode="json") == data["expectedResponse"]


def test_there_are_20_scenarios():
    assert len(SCENARIOS) == 20
