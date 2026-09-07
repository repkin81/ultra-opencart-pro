from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.opencart.client import OpenCartClient, OpenCartError
from app.opencart.csv_service import export_csv, import_products_csv
from app.opencart.schemas import CategoryPayload, OpenCartConnection, ProductPayload, SeoGenerateRequest, SeoGenerateResponse
from app.opencart.seo import generate_seo
from app.opencart.yml import build_yml

router = APIRouter(prefix="/opencart", tags=["OpenCart"])


@router.post("/test-connection")
def test_connection(config: OpenCartConnection):
    try:
        data = OpenCartClient(config.base_url, config.api_key, config.timeout).get("api/health")
        return {"ok": True, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/products")
def create_product(config: OpenCartConnection, product: ProductPayload):
    try:
        return OpenCartClient(config.base_url, config.api_key, config.timeout).post("api/products", json=product.model_dump(exclude_none=True))
    except OpenCartError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.put("/products/{product_id}")
def update_product(product_id: int, config: OpenCartConnection, product: ProductPayload):
    product.product_id = product_id
    try:
        return OpenCartClient(config.base_url, config.api_key, config.timeout).put(f"api/products/{product_id}", json=product.model_dump(exclude_none=True))
    except OpenCartError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/products/{product_id}")
def delete_product(product_id: int, config: OpenCartConnection):
    try:
        return OpenCartClient(config.base_url, config.api_key, config.timeout).delete(f"api/products/{product_id}")
    except OpenCartError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/categories")
def create_category(config: OpenCartConnection, category: CategoryPayload):
    try:
        return OpenCartClient(config.base_url, config.api_key, config.timeout).post("api/categories", json=category.model_dump(exclude_none=True))
    except OpenCartError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/seo/generate", response_model=SeoGenerateResponse)
def seo_generate(payload: SeoGenerateRequest):
    return generate_seo(payload)


@router.post("/csv/import")
def csv_import(content: str):
    rows = import_products_csv(content)
    return {"count": len(rows), "rows": rows}


@router.post("/csv/export")
def csv_export(rows: list[dict]):
    fields = sorted({key for row in rows for key in row})
    return Response(export_csv(rows, fields), media_type="text/csv; charset=utf-8")


@router.post("/yml")
def yml_feed(shop_name: str, shop_url: str, products: list[dict]):
    return Response(build_yml(shop_name, shop_url, products), media_type="application/xml; charset=utf-8")
