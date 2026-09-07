from app.opencart.client import OpenCartClient


def test_opencart_connector_url():
    client = OpenCartClient('https://shop.example', 'secret')
    assert client._url('api/health') == 'https://shop.example/index.php?route=extension/module/ultra_opencart_api/health'
    assert client._url('api/product?product_id=7') == 'https://shop.example/index.php?route=extension/module/ultra_opencart_api/product?product_id=7'
