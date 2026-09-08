from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WebhookEventIn(BaseModel):
    event_id: str | None = Field(default=None, max_length=128)
    event_type: Literal[
        "product.created", "product.updated", "product.deleted",
        "category.created", "category.updated", "category.deleted",
        "order.created", "order.updated", "inventory.changed", "price.changed"
    ]
    entity_type: str = Field(min_length=1, max_length=64)
    entity_id: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class WebhookEventOut(BaseModel):
    accepted: bool
    duplicate: bool = False
    event_id: str
    event_type: str
    connection_id: int
    queued: bool = False
