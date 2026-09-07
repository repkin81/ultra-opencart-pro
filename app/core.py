"""Application core services and startup helpers."""
from app.database import Base, engine
from app.models import Category, Product, User
from app.sync.migrations import migrate_sync_multistore


def init_database() -> None:
    """Create registered tables and apply lightweight schema migrations."""
    Base.metadata.create_all(bind=engine)
    migrate_sync_multistore()


__all__ = ["Base", "Category", "Product", "User", "engine", "init_database"]
