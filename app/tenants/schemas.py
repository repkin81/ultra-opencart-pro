from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    timezone: str = "UTC"
    currency: str = Field(default="RUB", min_length=3, max_length=8)
    max_users: int = Field(default=10, ge=1)
    max_connections: int = Field(default=10, ge=1)
    max_api_keys: int = Field(default=10, ge=1)
    max_events_per_day: int = Field(default=100000, ge=1)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    status: str | None = Field(default=None, min_length=2, max_length=32)
    timezone: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    max_users: int | None = Field(default=None, ge=1)
    max_connections: int | None = Field(default=None, ge=1)
    max_api_keys: int | None = Field(default=None, ge=1)
    max_events_per_day: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    status: str
    timezone: str
    currency: str
    max_users: int
    max_connections: int
    max_api_keys: int
    max_events_per_day: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
