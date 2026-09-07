from __future__ import annotations

from app.sync.connector import OpenCartConnector
from app.sync.schemas import SyncBatchIn, SyncItemIn
from app.sync.service import SyncService


class OpenCartPuller:
    """Reads OpenCart entities and converts them to a store-scoped Sync Core batch."""
    def __init__(self, connector: OpenCartConnector, service: SyncService, connection_id: int | None = None):
        self.connector = connector
        self.service = service
        self.connection_id = connection_id

    def pull(self, entity_type: str, page: int = 1, limit: int = 100, user_id: int | None = None):
        rows = self.connector.pull_batch(entity_type, page, limit)
        items: list[SyncItemIn] = []
        for row in rows:
            external_id = str(row.get("id") or row.get(f"{entity_type}_id") or "")
            if external_id:
                items.append(SyncItemIn(entity_type=entity_type, external_id=external_id, operation="upsert", payload=row))
        return self.service.enqueue(SyncBatchIn(connection_id=self.connection_id, items=items), user_id)
