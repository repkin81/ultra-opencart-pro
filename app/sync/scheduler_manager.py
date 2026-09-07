from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.sync.connection_models import OpenCartConnection, utcnow
from app.sync.connector import OpenCartConnector
from app.sync.scheduler import SyncScheduler

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MultiStoreSchedulerManager:
    """Background scheduler that runs enabled OpenCart stores independently."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._started_at: datetime | None = None
        self._last_cycle_at: datetime | None = None
        self._last_error: str | None = None
        self._cycles = 0
        self._stores_run = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @staticmethod
    def is_due(connection: OpenCartConnection, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        if connection.last_run_at is None:
            return True
        interval = max(5, int(connection.interval_seconds or 60))
        return now >= connection.last_run_at + timedelta(seconds=interval)

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self._stop_event.clear()
            self._started_at = _utcnow()
            self._last_error = None
            self._thread = threading.Thread(target=self._run, name="sync-multistore-scheduler", daemon=True)
            self._thread.start()
            return True

    def stop(self, timeout: float = 10.0) -> bool:
        with self._lock:
            thread = self._thread
            if thread is None:
                return False
            self._stop_event.set()
        thread.join(timeout=timeout)
        with self._lock:
            if not thread.is_alive():
                self._thread = None
        return not self.running

    def run_once(self) -> dict[str, Any]:
        started = _utcnow()
        results: list[dict[str, Any]] = []
        db = SessionLocal()
        try:
            connections = db.scalars(
                select(OpenCartConnection)
                .where(OpenCartConnection.enabled.is_(True))
                .order_by(OpenCartConnection.id)
            ).all()
        finally:
            db.close()

        for connection in connections:
            if not self.is_due(connection, started):
                continue
            results.append(self._run_connection(connection.id))

        self._cycles += 1
        self._last_cycle_at = _utcnow()
        return {
            "status": "ok",
            "started_at": started.isoformat(),
            "finished_at": self._last_cycle_at.isoformat(),
            "stores_checked": len(connections),
            "stores_run": len(results),
            "results": results,
        }

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "last_cycle_at": self._last_cycle_at.isoformat() if self._last_cycle_at else None,
            "last_error": self._last_error,
            "cycles": self._cycles,
            "stores_run": self._stores_run,
        }

    def _run_connection(self, connection_id: int) -> dict[str, Any]:
        db = SessionLocal()
        try:
            connection = db.get(OpenCartConnection, connection_id)
            if connection is None or not connection.enabled:
                return {"connection_id": connection_id, "status": "skipped"}
            if not self.is_due(connection):
                return {"connection_id": connection_id, "status": "not_due"}

            started = utcnow()
            connection.last_run_at = started
            connection.last_error = None
            db.commit()

            connector = OpenCartConnector(connection.base_url, connection.api_key, connection.timeout)
            scheduler = SyncScheduler(
                db,
                connector,
                connection_id=connection.id,
                interval_seconds=connection.interval_seconds,
                page_size=connection.page_size,
                max_retries=get_settings().sync_max_retries,
            )
            result = scheduler.run_cycle()

            connection = db.get(OpenCartConnection, connection_id)
            if connection is not None:
                if result.get("status") == "ok":
                    connection.last_success_at = utcnow()
                    connection.last_error = None
                else:
                    connection.last_error = str(result.get("error") or scheduler.last_error or "Sync failed")
                db.commit()

            self._stores_run += 1
            return {
                "connection_id": connection_id,
                "status": result.get("status", "error"),
                "result": result,
            }
        except Exception as exc:
            db.rollback()
            try:
                connection = db.get(OpenCartConnection, connection_id)
                if connection is not None:
                    connection.last_error = str(exc)
                    connection.last_run_at = utcnow()
                    db.commit()
            except Exception:
                db.rollback()
            self._stores_run += 1
            logger.exception("Automatic sync failed for OpenCart connection %s", connection_id)
            return {"connection_id": connection_id, "status": "error", "error": str(exc)}
        finally:
            db.close()

    def _run(self) -> None:
        settings = get_settings()
        poll_seconds = max(1, int(settings.sync_scheduler_poll_seconds))
        while not self._stop_event.is_set():
            try:
                self.run_once()
                self._last_error = None
            except Exception as exc:
                self._last_error = str(exc)
                logger.exception("Automatic multi-store scheduler cycle failed")
            self._stop_event.wait(poll_seconds)


scheduler_manager = MultiStoreSchedulerManager()
