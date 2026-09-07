from typing import Any

from app.opencart.client import OpenCartClient


class OpenCartSync:
    """High-level catalog synchronization facade for the OpenCart 3 connector."""

    def __init__(self, client: OpenCartClient):
        self.client = client

    def create_product(self, product: dict[str, Any]) -> Any:
        return self.client.post('api/createProduct', json=product)

    def list_products(self, limit: int = 100, offset: int = 0) -> Any:
        return self.client.get(f'api/products?limit={limit}&offset={offset}')

    def get_product(self, product_id: int) -> Any:
        return self.client.get(f'api/product?product_id={product_id}')

    def update_product(self, product_id: int, product: dict[str, Any]) -> Any:
        return self.client.put(f'api/product?product_id={product_id}', json=product)

    def delete_product(self, product_id: int) -> Any:
        return self.client.delete(f'api/product?product_id={product_id}')

    def create_category(self, category: dict[str, Any]) -> Any:
        return self.client.post('api/createCategory', json=category)

    def list_categories(self, limit: int = 100, offset: int = 0) -> Any:
        return self.client.get(f'api/categories?limit={limit}&offset={offset}')

    def get_category(self, category_id: int) -> Any:
        return self.client.get(f'api/category?category_id={category_id}')

    def update_category(self, category_id: int, category: dict[str, Any]) -> Any:
        return self.client.put(f'api/category?category_id={category_id}', json=category)

    def delete_category(self, category_id: int) -> Any:
        return self.client.delete(f'api/category?category_id={category_id}')

    def bulk_stock_price(self, items: list[dict[str, Any]]) -> Any:
        return self.client.post('api/bulkStockPrice', json={'items': items})

    def test(self) -> Any:
        return self.client.get('api/health')
