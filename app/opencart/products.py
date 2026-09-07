from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


def list_products(db: Session, limit: int = 100, offset: int = 0) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id).offset(offset).limit(limit)))


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def create_product(db: Session, data: dict[str, Any]) -> Product:
    product = Product(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, data: dict[str, Any]) -> Product:
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
