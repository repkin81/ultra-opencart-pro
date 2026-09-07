from sqlalchemy import inspect, text

from app.database import engine


def migrate_sync_multistore() -> None:
    """Upgrade existing databases for per-store sync isolation.

    Existing rows keep connection_id=NULL and therefore remain compatible with
    the legacy single-store API until a connection is explicitly selected.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if not {"sync_jobs", "sync_items", "sync_mappings"}.issubset(tables):
        return

    with engine.begin() as conn:
        for table in ("sync_jobs", "sync_items"):
            columns = {c["name"] for c in inspect(conn).get_columns(table)}
            if "connection_id" not in columns:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN connection_id INTEGER"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_connection_id ON {table} (connection_id)"))

        columns = {c["name"] for c in inspect(conn).get_columns("sync_mappings")}
        if "connection_id" not in columns:
            conn.execute(text("ALTER TABLE sync_mappings RENAME TO sync_mappings_legacy"))
            conn.execute(text("""
                CREATE TABLE sync_mappings (
                    id INTEGER PRIMARY KEY,
                    connection_id INTEGER,
                    entity_type VARCHAR(64) NOT NULL,
                    external_id VARCHAR(128) NOT NULL,
                    core_id VARCHAR(128) NOT NULL,
                    checksum VARCHAR(64),
                    updated_at DATETIME,
                    CONSTRAINT uq_sync_mapping_connection_external
                        UNIQUE (connection_id, entity_type, external_id),
                    FOREIGN KEY(connection_id) REFERENCES open_cart_connections(id) ON DELETE CASCADE
                )
            """))
            conn.execute(text("""
                INSERT INTO sync_mappings
                    (id, connection_id, entity_type, external_id, core_id, checksum, updated_at)
                SELECT id, NULL, entity_type, external_id, core_id, checksum, updated_at
                FROM sync_mappings_legacy
            """))
            conn.execute(text("DROP TABLE sync_mappings_legacy"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sync_mappings_connection_id ON sync_mappings (connection_id)"))
