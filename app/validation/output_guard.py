"""Last gate before anything leaves this service. Whatever a provider (mock now, Gemini later) returns is
UNTRUSTED text. We (1) check the structure + cross-field rules (schemas), then (2) the two rules that need
context: check 6 (no approval claims in the reply) and check 9 / UNMATCHED ids (ids must exist in the catalog
we were given)."""
import re
from typing import Any

from pydantic import ValidationError

from app.schemas import AiRequest, AiResponse
from app.text import normalize_arabic


class OutputRejected(Exception):
    """The provider's answer broke the contract. The orchestrator turns this into a safe fallback reply."""


# Patterns run on normalize_arabic(reply): ة->ه, أ->ا ... so "تمت الموافقة" is matched as "تمت الموافقه".
_APPROVAL_PATTERNS = [
    re.compile(r"\bتمت?\s+(?:ال)?(?:تاكيد|اعتماد|قبول|موافقه)"),
    re.compile(r"\b(?:طلبك|الطلب|الاوردر)\s+(?:اتاكد|اتقبل|اتعتمد|اتوافق|موكد|معتمد|مقبول)\b"),
    re.compile(r"\b(?:اتقبل|اتعتمد)\b"),
    re.compile(r"\b(?:order|request)\b[^.!?\n]{0,40}\b(?:is|has been|was|been)\s+(?:approved|confirmed|accepted)\b"),
    re.compile(r"\b(?:approved|confirmed|accepted)\b[^.!?\n]{0,20}\byour\s+order\b"),
]


def claims_approval(reply: str) -> bool:
    text = normalize_arabic(reply)
    return any(p.search(text) for p in _APPROVAL_PATTERNS)


def validate_output(raw: Any, request: AiRequest) -> AiResponse:
    if not isinstance(raw, dict):
        raise OutputRejected("provider output is not a JSON object")
    try:
        response = AiResponse.model_validate(raw)
    except ValidationError as exc:
        raise OutputRejected(f"schema/consistency violation: {exc.error_count()} error(s): {exc.errors()[0]['msg']}") from exc

    if claims_approval(response.reply):                                              # check 6
        raise OutputRejected("reply claims the order is approved/confirmed")

    known = request.catalog_ids
    if response.productReference and response.productReference.catalogItemId not in known:   # check 9
        raise OutputRejected("productReference.catalogItemId is not in the catalog context")
    if response.orderCandidate:
        for item in response.orderCandidate.items:
            if item.catalogItemId is not None and item.catalogItemId not in known:
                raise OutputRejected("orderCandidate item id is not in the catalog context")
    return response
