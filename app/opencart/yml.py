from xml.etree.ElementTree import Element, SubElement, tostring
from xml.sax.saxutils import escape


def build_yml(shop_name: str, shop_url: str, products: list[dict]) -> str:
    catalog = Element("yml_catalog", date="2026-09-07 00:00")
    shop = SubElement(catalog, "shop")
    SubElement(shop, "name").text = shop_name
    SubElement(shop, "company").text = shop_name
    SubElement(shop, "url").text = shop_url
    offers = SubElement(shop, "offers")
    for item in products:
        offer = SubElement(offers, "offer", id=str(item.get("id") or item.get("product_id") or "0"), available="true" if item.get("status", True) else "false")
        SubElement(offer, "name").text = str(item.get("name", ""))
        SubElement(offer, "url").text = str(item.get("url", ""))
        SubElement(offer, "price").text = str(item.get("price", 0))
        SubElement(offer, "currencyId").text = str(item.get("currency", "RUB"))
        if item.get("category_id") is not None:
            SubElement(offer, "categoryId").text = str(item["category_id"])
        if item.get("picture"):
            SubElement(offer, "picture").text = str(item["picture"])
        if item.get("description"):
            SubElement(offer, "description").text = escape(str(item["description"]))
    return '<?xml version="1.0" encoding="UTF-8"?>' + tostring(catalog, encoding="unicode")
