from datetime import datetime, timedelta

from app.sync.connection_models import OpenCartConnection
from app.sync.scheduler_manager import MultiStoreSchedulerManager


def test_manager_runs_connection_without_previous_run():
    connection = OpenCartConnection(
        id=1,
        name="Store",
        base_url="https://shop.example.com",
        api_key="secret",
        enabled=True,
        interval_seconds=60,
        page_size=100,
    )
    assert MultiStoreSchedulerManager.is_due(connection, datetime(2026, 9, 7, 12, 0, 0))


def test_manager_respects_connection_interval():
    connection = OpenCartConnection(
        id=1,
        name="Store",
        base_url="https://shop.example.com",
        api_key="secret",
        enabled=True,
        interval_seconds=300,
        page_size=100,
        last_run_at=datetime(2026, 9, 7, 12, 0, 0),
    )
    assert not MultiStoreSchedulerManager.is_due(connection, datetime(2026, 9, 7, 12, 4, 59))
    assert MultiStoreSchedulerManager.is_due(connection, datetime(2026, 9, 7, 12, 5, 0))
