"""Application core services and startup helpers."""
from app.database import Base, engine
from app.models import Category, Product, Tenant, User
from app.sync.migrations import migrate_sync_multistore
from app.tenants.bootstrap import ensure_default_tenant
from app.tenants.migrations import migrate_tenant_columns


def init_database() -> None:
    """Create registered tables and apply lightweight schema migrations."""
    Base.metadata.create_all(bind=engine)
    migrate_sync_multistore()
    migrate_tenant_columns()
    ensure_default_tenant()


__all__ = ["Base", "Category", "Product", "Tenant", "User", "engine", "init_database"]
