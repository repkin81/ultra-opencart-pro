from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


def list_categories(db: Session, limit: int = 100, offset: int = 0) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id).offset(offset).limit(limit)))


def get_category(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def create_category(db: Session, **data) -> Category:
    item = Category(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_products(db: Session, limit: int = 100, offset: int = 0) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.id).offset(offset).limit(limit)))


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)
