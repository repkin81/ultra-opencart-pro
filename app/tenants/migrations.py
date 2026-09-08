from sqlalchemy import inspect, text

from app.database import engine


def migrate_tenant_columns() -> None:
    """Add tenant_id to existing tenant-owned tables without breaking old SQLite DBs."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "tenants" not in tables:
        return

    tenant_owned = [
        "open_cart_connections",
        "sync_jobs",
        "sync_items",
        "sync_mappings",
    ]
    with engine.begin() as conn:
        for table in tenant_owned:
            if table not in tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "tenant_id" not in columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id INTEGER"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table} (tenant_id)"))
