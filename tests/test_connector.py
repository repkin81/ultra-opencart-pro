from app.sync.connector import OpenCartConnector


def test_connector_builds_product_pull_request(monkeypatch):
    connector = OpenCartConnector("https://shop.example", "secret")
    captured = {}

    def fake_get(path, **kwargs):
        captured["path"] = path
        captured["kwargs"] = kwargs
        return {"products": [{"product_id": 10}]}

    monkeypatch.setattr(connector.client, "get", fake_get)
    result = connector.list_products(page=2, limit=25)

    assert result == [{"product_id": 10}]
    assert captured["path"] == "api/products"
    assert captured["kwargs"]["params"] == {"page": 2, "limit": 25}
