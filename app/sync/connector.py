from __future__ import annotations

from typing import Any

from app.opencart.client import OpenCartClient, OpenCartError


class OpenCartConnector:
    """OpenCart API adapter used by the bidirectional Sync Core."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.client = OpenCartClient(base_url, api_key, timeout)

    def heartbeat(self) -> dict[str, Any]:
        return self.client.get("api/health")

    @staticmethod
    def _unwrap(data: Any, key: str) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            value = data.get(key, data.get("data", []))
            return value if isinstance(value, list) else [value]
        return data if isinstance(data, list) else []

    def list_products(self, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        data = self.client.get("api/products", params={"limit": limit, "offset": (page - 1) * limit})
        return self._unwrap(data, "products")

    def list_categories(self, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        data = self.client.get("api/categories", params={"limit": limit, "offset": (page - 1) * limit})
        return self._unwrap(data, "categories")

    def get_product(self, product_id: int) -> dict[str, Any]:
        data = self.client.get("api/product", params={"product_id": product_id})
        return data.get("product", data) if isinstance(data, dict) else data

    def get_category(self, category_id: int) -> dict[str, Any]:
        data = self.client.get("api/category", params={"category_id": category_id})
        return data.get("category", data) if isinstance(data, dict) else data

    def pull_batch(self, entity_type: str, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        if entity_type == "product":
            return self.list_products(page, limit)
        if entity_type == "category":
            return self.list_categories(page, limit)
        raise ValueError(f"Unsupported entity type: {entity_type}")

    def push_product(self, payload: dict[str, Any], product_id: int | None = None) -> dict[str, Any]:
        try:
            if product_id:
                data = self.client.put("api/product", params={"product_id": product_id}, json=payload)
            else:
                data = self.client.post("api/createProduct", json=payload)
            return data if isinstance(data, dict) else {"data": data}
        except OpenCartError:
            raise

    def push_category(self, payload: dict[str, Any], category_id: int | None = None) -> dict[str, Any]:
        if category_id:
            data = self.client.put("api/category", params={"category_id": category_id}, json=payload)
        else:
            data = self.client.post("api/createCategory", json=payload)
        return data if isinstance(data, dict) else {"data": data}

    def delete_product(self, product_id: int) -> Any:
        return self.client.delete("api/product", params={"product_id": product_id})

    def delete_category(self, category_id: int) -> Any:
        return self.client.delete("api/category", params={"category_id": category_id})
