from pydantic import BaseModel, Field


class ConnectorConfig(BaseModel):
    base_url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    timeout: float = Field(default=30.0, gt=0, le=120)


class PullRequest(BaseModel):
    entity_type: str = Field(pattern="^(product|category)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=1000)
    connection_id: int | None = Field(default=None, ge=1)
