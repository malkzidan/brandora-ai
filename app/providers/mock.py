"""Replays the golden answers in mock_data/scenarios/*.json, matched by the customer's message.
Lets us build and test the whole pipeline (schemas, guard, API) before any LLM exists."""
import json
from pathlib import Path
from typing import Any

from app.schemas import AiRequest

NOT_UNDERSTOOD = {
    "intent": "UNKNOWN",
    "reply": "معلش، مش قادر أفهم قصدك. ممكن توضح أكتر؟",
    "productReference": None,
    "requiresReview": False,
    "orderCandidate": None,
}


class MockProvider:
    def __init__(self, mock_data_dir: Path):
        self._by_message: dict[str, dict[str, Any]] = {}
        for path in sorted((mock_data_dir / "scenarios").glob("[0-9]*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self._by_message[data["request"]["message"].strip()] = data["expectedResponse"]

    async def generate(self, request: AiRequest) -> dict[str, Any]:
        return json.loads(json.dumps(self._by_message.get(request.message.strip(), NOT_UNDERSTOOD)))  # deep copy
