"""What we send back (contract schema v1.0). The backend uses whitelist + forbidNonWhitelisted,
so ANY extra or missing field gets our answer rejected -> every model here is extra="forbid"."""
import uuid
from enum import Enum
from typing import Annotated, Literal

from pydantic import (AfterValidator, BaseModel, ConfigDict, Field, StrictInt,
                      field_validator, model_validator)


class Intent(str, Enum):
    GREETING = "GREETING"
    INQUIRY_PRODUCT = "INQUIRY_PRODUCT"
    INQUIRY_PRICE = "INQUIRY_PRICE"
    INQUIRY_AVAILABILITY = "INQUIRY_AVAILABILITY"
    ORDER_CREATE = "ORDER_CREATE"
    ORDER_MODIFY = "ORDER_MODIFY"
    ORDER_CANCEL = "ORDER_CANCEL"
    UP_FOLLOW = "UP_FOLLOW"
    INFO_GENERAL = "INFO_GENERAL"
    COMPLAINT = "COMPLAINT"
    THANKYOU = "THANKYOU"
    PRODUCT_IMAGE_REQUEST = "PRODUCT_IMAGE_REQUEST"
    UNKNOWN = "UNKNOWN"


class ReviewReason(str, Enum):  # only the 7 values the AI may send (ITEM_INACTIVE / INSUFFICIENT_STOCK are backend-only)
    AMBIGUOUS_ITEM = "AMBIGUOUS_ITEM"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    ATTRIBUTE_NOT_IN_CATALOG = "ATTRIBUTE_NOT_IN_CATALOG"
    UNMATCHED_ITEM = "UNMATCHED_ITEM"
    MISSING_DELIVERY_ADDRESS = "MISSING_DELIVERY_ADDRESS"
    CUSTOMER_REQUESTED_CUSTOM = "CUSTOMER_REQUESTED_CUSTOM"
    OTHER = "OTHER"


PRODUCT_REFERENCE_INTENTS = {
    Intent.PRODUCT_IMAGE_REQUEST, Intent.INQUIRY_PRODUCT, Intent.INQUIRY_PRICE, Intent.INQUIRY_AVAILABILITY,
}


def _must_be_uuid(value: str) -> str:
    uuid.UUID(value)  # raises ValueError -> pydantic reports a validation error
    return value


UuidStr = Annotated[str, AfterValidator(_must_be_uuid)]
Confidence = Annotated[float, Field(ge=0, le=1)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProductReference(_Strict):
    catalogItemId: UuidStr


class OrderCandidateItem(_Strict):
    rawText: str = Field(min_length=1, max_length=200)
    catalogItemId: UuidStr | None
    variantId: None                       # always null in schema 1.0
    variant: dict[str, str]
    quantity: Annotated[StrictInt, Field(ge=1, le=1000)]
    selectedOptions: list[str] = Field(max_length=10)
    note: str | None = Field(max_length=300)
    confidence: Confidence

    @field_validator("variant")
    @classmethod
    def _variant_limits(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 10 or any(len(k) > 50 for k in v) or any(len(x) > 100 for x in v.values()):
            raise ValueError("variant: max 10 keys, key<=50 chars, value<=100 chars")
        return v

    @field_validator("selectedOptions")
    @classmethod
    def _options_limits(cls, v: list[str]) -> list[str]:
        if any(len(x) > 100 for x in v):
            raise ValueError("selectedOptions: each <=100 chars")
        return v


class OrderCandidate(_Strict):
    schemaVersion: Literal["1.0"]
    items: list[OrderCandidateItem] = Field(min_length=1, max_length=20)
    deliveryAddress: str | None = Field(max_length=500)
    requestedDetails: str | None = Field(max_length=500)
    notes: str | None = Field(max_length=500)
    confidence: Confidence
    requiresReview: bool
    reviewReasons: list[ReviewReason]

    @model_validator(mode="after")
    def _consistency(self):
        reasons = self.reviewReasons
        if len(set(reasons)) != len(reasons):                       # check 3 (no duplicates)
            raise ValueError("reviewReasons must not contain duplicates")
        if self.requiresReview and not reasons:                     # check 3
            raise ValueError("requiresReview=true needs at least one reviewReason")
        if not self.requiresReview and reasons:                     # check 3
            raise ValueError("requiresReview=false needs reviewReasons=[]")
        if any(i.catalogItemId is None for i in self.items):        # check 4
            if not self.requiresReview or ReviewReason.UNMATCHED_ITEM not in reasons:
                raise ValueError("an item with catalogItemId=null requires requiresReview=true + UNMATCHED_ITEM")
        return self


class AiResponse(_Strict):
    intent: Intent
    reply: str = Field(min_length=1, max_length=2000)
    productReference: ProductReference | None
    requiresReview: bool
    orderCandidate: OrderCandidate | None

    @model_validator(mode="after")
    def _consistency(self):
        if self.orderCandidate is not None and self.intent != Intent.ORDER_CREATE:      # check 1
            raise ValueError("orderCandidate is allowed only for ORDER_CREATE")
        expected_review = self.orderCandidate.requiresReview if self.orderCandidate else False
        if self.requiresReview != expected_review:                                       # check 2
            raise ValueError("top-level requiresReview must equal orderCandidate.requiresReview (false if null)")
        if self.productReference is not None and self.intent not in PRODUCT_REFERENCE_INTENTS:  # check 8
            raise ValueError("productReference is allowed only for product/price/availability/image intents")
        return self
