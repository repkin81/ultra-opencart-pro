from app.sync.models import SyncItem, SyncJob, SyncMapping
from app.sync.schemas import SyncBatchIn


def test_sync_entities_have_connection_scope():
    assert "connection_id" in SyncJob.__table__.c
    assert "connection_id" in SyncItem.__table__.c
    assert "connection_id" in SyncMapping.__table__.c


def test_batch_accepts_connection_id():
    batch = SyncBatchIn(connection_id=7, items=[])
    assert batch.connection_id == 7
