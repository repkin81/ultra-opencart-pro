from __future__ import annotations

from typing import Any

from app.opencart.client import OpenCartClient, OpenCartError


class OpenCartConnector:
    """Thin adapter between Sync Core and an OpenCart instance."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.client = OpenCartClient(base_url, api_key, timeout)

    def heartbeat(self) -> dict[str, Any]:
        return self.client.get("api/health")

    def list_products(self, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        data = self.client.get("api/products", params={"page": page, "limit": limit})
        if isinstance(data, dict):
            return data.get("products", data.get("data", []))
        return data

    def list_categories(self, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        data = self.client.get("api/categories", params={"page": page, "limit": limit})
        if isinstance(data, dict):
            return data.get("categories", data.get("data", []))
        return data

    def pull_batch(self, entity_type: str, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        if entity_type == "product":
            return self.list_products(page, limit)
        if entity_type == "category":
            return self.list_categories(page, limit)
        raise ValueError(f"Unsupported entity type: {entity_type}")

    def push_product(self, payload: dict[str, Any], product_id: int | None = None) -> dict[str, Any]:
        try:
            if product_id:
                return self.client.put(f"api/products/{product_id}", json=payload)
            return self.client.post("api/products", json=payload)
        except OpenCartError:
            raise
