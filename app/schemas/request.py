"""What NestJS sends us (contract section 2). Lenient on purpose: the backend may add fields and
the exact shape of `conversation` / `customer` is not final, so we accept extras instead of crashing."""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CatalogContextItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    description: str | None = None
    category: str | None = None
    basePrice: str | int | float | None = None   # backend sends Decimal as a string, e.g. "299"
    trackInventory: bool = False
    stockQuantity: int | None = None
    attributes: dict[str, Any] | None = None
    isActive: bool = True


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: str = "CUSTOMER"            # CUSTOMER | AI | OWNER
    content: str | None = None
    text: str | None = None           # tolerate either field name until the backend confirms

    @property
    def body(self) -> str:
        return self.content or self.text or ""


class AiRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    business: dict[str, Any] = Field(default_factory=dict)
    customer: dict[str, Any] = Field(default_factory=dict)
    conversation: list[ConversationMessage] = Field(default_factory=list)
    catalog: list[CatalogContextItem] = Field(default_factory=list)
    businessKnowledge: dict[str, Any] = Field(default_factory=dict)
    message: str

    @property
    def catalog_ids(self) -> set[str]:
        return {item.id for item in self.catalog}
