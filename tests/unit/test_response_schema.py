import copy
import pytest
from pydantic import ValidationError

from app.schemas import AiResponse

UUID = "3f6c2a9e-7b1d-4c58-9a3e-1d2f5b8c0a41"


def item(**over):
    base = {"rawText": "تيشيرت أسود XL", "catalogItemId": UUID, "variantId": None, "variant": {"size": "XL"},
            "quantity": 1, "selectedOptions": [], "note": None, "confidence": 0.9}
    base.update(over)
    return base


def cand(**over):
    base = {"schemaVersion": "1.0", "items": [item()], "deliveryAddress": None, "requestedDetails": None, "notes": None,
            "confidence": 0.9, "requiresReview": False, "reviewReasons": []}
    base.update(over)
    return base


def resp(**over):
    base = {"intent": "GREETING", "reply": "أهلاً", "productReference": None, "requiresReview": False, "orderCandidate": None}
    base.update(over)
    return base


def test_valid_plain_response():
    assert AiResponse.model_validate(resp()).intent.value == "GREETING"


def test_valid_order_candidate():
    assert AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand())).orderCandidate


@pytest.mark.parametrize("missing", ["intent", "reply", "productReference", "requiresReview", "orderCandidate"])
def test_every_top_level_field_is_required(missing):
    data = resp(); data.pop(missing)
    with pytest.raises(ValidationError):
        AiResponse.model_validate(data)


@pytest.mark.parametrize("extra", [{"deliveryFee": 50}, {"total": 100}, {"needsClarification": True}, {"orderId": "1"}])
def test_extra_fields_are_rejected(extra):
    with pytest.raises(ValidationError):
        AiResponse.model_validate({**resp(), **extra})


def test_prices_are_rejected_inside_candidate_items():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(items=[item(price=200, total=400)])))


def test_unknown_intent_rejected():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="SMALL_TALK"))


@pytest.mark.parametrize("reply", ["", "x" * 2001])
def test_reply_length(reply):
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(reply=reply))


def test_check1_candidate_only_for_order_create():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="INQUIRY_PRICE", orderCandidate=cand()))


def test_check2_top_level_review_must_match_candidate():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", requiresReview=True, orderCandidate=cand()))
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(requiresReview=True))


def test_check3_review_reasons_rules():
    bad = [cand(requiresReview=True, reviewReasons=[]),
           cand(requiresReview=False, reviewReasons=["LOW_CONFIDENCE"]),
           cand(requiresReview=True, reviewReasons=["LOW_CONFIDENCE", "LOW_CONFIDENCE"])]
    for c in bad:
        with pytest.raises(ValidationError):
            AiResponse.model_validate(resp(intent="ORDER_CREATE", requiresReview=c["requiresReview"], orderCandidate=c))


def test_backend_only_review_reasons_are_rejected():
    for reason in ("ITEM_INACTIVE", "INSUFFICIENT_STOCK"):
        c = cand(requiresReview=True, reviewReasons=[reason])
        with pytest.raises(ValidationError):
            AiResponse.model_validate(resp(intent="ORDER_CREATE", requiresReview=True, orderCandidate=c))


def test_check4_null_catalog_id_needs_unmatched_item():
    c = cand(items=[item(catalogItemId=None)])
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=c))
    ok = cand(items=[item(catalogItemId=None)], requiresReview=True, reviewReasons=["UNMATCHED_ITEM"])
    assert AiResponse.model_validate(resp(intent="ORDER_CREATE", requiresReview=True, orderCandidate=ok))


def test_check5_variant_id_must_be_null():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(items=[item(variantId=UUID)])))


@pytest.mark.parametrize("intent", ["GREETING", "INFO_GENERAL", "ORDER_CREATE", "COMPLAINT", "UNKNOWN", "THANKYOU"])
def test_check8_product_reference_only_for_product_intents(intent):
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent=intent, productReference={"catalogItemId": UUID}))


@pytest.mark.parametrize("intent", ["PRODUCT_IMAGE_REQUEST", "INQUIRY_PRODUCT", "INQUIRY_PRICE", "INQUIRY_AVAILABILITY"])
def test_product_reference_allowed(intent):
    assert AiResponse.model_validate(resp(intent=intent, productReference={"catalogItemId": UUID}))


def test_catalog_item_id_must_be_uuid():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="INQUIRY_PRICE", productReference={"catalogItemId": "product-123"}))


@pytest.mark.parametrize("over", [{"quantity": 0}, {"quantity": 1001}, {"quantity": 1.5}, {"quantity": True},
                                  {"confidence": 1.2}, {"confidence": -0.1}, {"rawText": ""}, {"rawText": "x" * 201},
                                  {"note": "x" * 301}, {"selectedOptions": ["a"] * 11},
                                  {"variant": {f"k{i}": "v" for i in range(11)}}, {"variant": {"k" * 51: "v"}},
                                  {"variant": {"size": "v" * 101}}, {"variant": {"size": 5}}])
def test_item_limits(over):
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(items=[item(**over)])))


def test_candidate_item_count_limits():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(items=[])))
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(items=[item() for _ in range(21)])))


def test_schema_version_must_be_1_0():
    with pytest.raises(ValidationError):
        AiResponse.model_validate(resp(intent="ORDER_CREATE", orderCandidate=cand(schemaVersion="1.1")))
