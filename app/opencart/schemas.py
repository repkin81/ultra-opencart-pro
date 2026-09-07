from pydantic import BaseModel, Field


class OpenCartConnection(BaseModel):
    base_url: str
    api_key: str = Field(min_length=1)
    timeout: float = Field(default=30, gt=0, le=120)


class ProductPayload(BaseModel):
    product_id: int | None = None
    model: str = ""
    sku: str = ""
    name: str
    description: str = ""
    meta_title: str = ""
    meta_description: str = ""
    meta_keyword: str = ""
    price: float = Field(default=0, ge=0)
    quantity: int = Field(default=0, ge=0)
    status: bool = True
    categories: list[int] = []


class CategoryPayload(BaseModel):
    category_id: int | None = None
    name: str
    description: str = ""
    meta_title: str = ""
    meta_description: str = ""
    meta_keyword: str = ""
    parent_id: int = Field(default=0, ge=0)
    status: bool = True


class SeoGenerateRequest(BaseModel):
    product_name: str
    model: str = ""
    part_number: str = ""
    compatible_models: list[str] = []
    keywords: list[str] = []
    language: str = "ru"


class SeoGenerateResponse(BaseModel):
    title: str
    description: str
    meta_title: str
    meta_description: str
    meta_keyword: str
    slug: str
