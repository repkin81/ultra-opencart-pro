from typing import Any

from app.opencart.client import OpenCartClient


class OpenCartSync:
    """High-level catalog synchronization facade."""

    def __init__(self, client: OpenCartClient):
        self.client = client

    def create_product(self, product: dict[str, Any]) -> Any:
        return self.client.post("api/products", json=product)

    def update_product(self, product_id: int, product: dict[str, Any]) -> Any:
        return self.client.put(f"api/products/{product_id}", json=product)

    def delete_product(self, product_id: int) -> Any:
        return self.client.delete(f"api/products/{product_id}")

    def create_category(self, category: dict[str, Any]) -> Any:
        return self.client.post("api/categories", json=category)

    def test(self) -> Any:
        return self.client.get("api/health")
