from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: HttpUrl
    api_key: str = Field(min_length=1)
    timeout: int = Field(default=30, ge=1, le=120)
    enabled: bool = True
    interval_seconds: int = Field(default=60, ge=5, le=86400)
    page_size: int = Field(default=100, ge=1, le=1000)


class ConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_url: HttpUrl | None = None
    api_key: str | None = Field(default=None, min_length=1)
    timeout: int | None = Field(default=None, ge=1, le=120)
    enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=5, le=86400)
    page_size: int | None = Field(default=None, ge=1, le=1000)


class ConnectionOut(BaseModel):
    id: int
    name: str
    base_url: str
    timeout: int
    enabled: bool
    interval_seconds: int
    page_size: int
    has_api_key: bool
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestOut(BaseModel):
    connection_id: int
    ok: bool
    response: dict | None = None
    error: str | None = None
