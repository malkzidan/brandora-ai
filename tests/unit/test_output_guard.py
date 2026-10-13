import pytest

from app.schemas import AiRequest
from app.validation.output_guard import OutputRejected, claims_approval, validate_output

KNOWN = "3f6c2a9e-7b1d-4c58-9a3e-1d2f5b8c0a41"
UNKNOWN = "00000000-0000-4000-8000-000000000000"


@pytest.mark.parametrize("reply", [
    "تم تأكيد طلبك", "تم تاكيد الاوردر", "تمت الموافقة على طلبك", "طلبك اتأكد", "الأوردر اتقبل", "طلبك مؤكد",
    "تم اعتماد الطلب", "تم قبول طلبك", "Your order is confirmed", "Your order has been approved",
    "We have confirmed your order", "The order was accepted",
])
def test_detects_approval_claims(reply):
    assert claims_approval(reply)


@pytest.mark.parametrize("reply", [
    "تمام، هجهز طلبك للمراجعة.", "تحب أأكد الطلب؟", "هنراجع الطلب ونأكد معاك", "سعر الهودي 520 جنيه.",
    "تمام، تحبي مقاس إيه؟", "Your order will be reviewed shortly", "Can you confirm the size?",
])
def test_allows_normal_replies(reply):
    assert not claims_approval(reply)


def req(catalog_ids=(KNOWN,)):
    return AiRequest.model_validate({"message": "x", "catalog": [{"id": i, "name": "n"} for i in catalog_ids]})


def good(**over):
    base = {"intent": "INQUIRY_PRICE", "reply": "سعر التيشيرت 299 جنيه.", "productReference": {"catalogItemId": KNOWN},
            "requiresReview": False, "orderCandidate": None}
    base.update(over)
    return base


def test_valid_output_passes():
    assert validate_output(good(), req()).productReference.catalogItemId == KNOWN


def test_check9_product_reference_must_be_in_catalog():
    with pytest.raises(OutputRejected):
        validate_output(good(productReference={"catalogItemId": UNKNOWN}), req())


def test_candidate_item_must_be_in_catalog():
    item = {"rawText": "x", "catalogItemId": UNKNOWN, "variantId": None, "variant": {}, "quantity": 1,
            "selectedOptions": [], "note": None, "confidence": 0.9}
    cand = {"schemaVersion": "1.0", "items": [item], "deliveryAddress": None, "requestedDetails": None, "notes": None,
            "confidence": 0.9, "requiresReview": False, "reviewReasons": []}
    with pytest.raises(OutputRejected):
        validate_output(good(intent="ORDER_CREATE", productReference=None, orderCandidate=cand), req())


def test_check6_approval_claim_rejected():
    with pytest.raises(OutputRejected):
        validate_output(good(reply="تم تأكيد طلبك"), req())


@pytest.mark.parametrize("raw", [None, "text", [], 5, {"intent": "GREETING"}, {}])
def test_garbage_is_rejected(raw):
    with pytest.raises(OutputRejected):
        validate_output(raw, req())
