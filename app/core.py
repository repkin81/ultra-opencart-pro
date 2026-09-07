"""Application core services and startup helpers."""
from app.database import Base, engine
from app.models import Category, Product, User


def init_database() -> None:
    """Create all registered tables for the configured database."""
    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "Category", "Product", "User", "engine", "init_database"]
