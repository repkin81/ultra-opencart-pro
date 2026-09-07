from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SyncItemIn(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=128)
    operation: Literal["upsert", "delete"] = "upsert"
    payload: dict[str, Any] | None = None


class SyncBatchIn(BaseModel):
    direction: Literal["opencart_to_core", "core_to_opencart"] = "opencart_to_core"
    connection_id: int | None = Field(default=None, ge=1)
    items: list[SyncItemIn] = Field(default_factory=list, max_length=1000)


class SyncJobOut(BaseModel):
    id: int
    connection_id: int | None
    direction: str
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    model_config = {"from_attributes": True}


class SyncPushOut(BaseModel):
    job_id: int
    accepted: int
    skipped: int
