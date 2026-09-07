from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sync.connector import OpenCartConnector
from app.sync.models import SyncItem, SyncJob
from app.sync.schemas import SyncBatchIn, SyncItemIn
from app.sync.service import SyncService
from app.sync.worker import SyncWorker

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncScheduler:
    """Automatic single-process scheduler for one OpenCart connection."""
    _lock = threading.Lock()

    def __init__(self, db: Session, connector: OpenCartConnector, connection_id: int | None = None,
                 interval_seconds: int = 60, page_size: int = 100, max_retries: int = 3):
        self.db = db
        self.connector = connector
        self.connection_id = connection_id
        self.interval_seconds = max(5, interval_seconds)
        self.page_size = max(1, min(page_size, 1000))
        self.max_retries = max(0, max_retries)
        self.last_run_at = None
        self.last_error = None
        self.last_result: dict[str, Any] = {}
        self._retry_counts: dict[int, int] = {}

    def run_cycle(self):
        if not self._lock.acquire(blocking=False):
            return {"status": "locked", "message": "Another scheduler cycle is already running"}
        started = utcnow()
        try:
            self.last_run_at = started
            self.last_error = None
            pulled = {"product": self._pull_all("product"), "category": self._pull_all("category")}
            processed = self._drain_queue()
            result = {"status": "ok", "connection_id": self.connection_id, "started_at": started.isoformat(),
                      "finished_at": utcnow().isoformat(), "pulled": pulled, "processed_jobs": processed}
            self.last_result = result
            return result
        except Exception as exc:
            self.db.rollback()
            self.last_error = str(exc)
            result = {"status": "error", "connection_id": self.connection_id, "error": str(exc)}
            self.last_result = result
            logger.exception("Sync scheduler cycle failed")
            return result
        finally:
            self._lock.release()

    def run_forever(self):
        while True:
            self.run_cycle()
            time.sleep(self.interval_seconds)

    def _pull_all(self, entity_type: str) -> int:
        page = 1
        total = 0
        while True:
            rows = self.connector.pull_batch(entity_type, page, self.page_size)
            if not rows:
                break
            items: list[SyncItemIn] = []
            for row in rows:
                external_id = str(row.get("id") or row.get(f"{entity_type}_id") or "")
                if external_id:
                    items.append(SyncItemIn(entity_type=entity_type, external_id=external_id, operation="upsert", payload=row))
            if items:
                SyncService(self.db).enqueue(SyncBatchIn(direction="opencart_to_core", connection_id=self.connection_id, items=items))
                total += len(items)
            if len(rows) < self.page_size:
                break
            page += 1
        return total

    def _drain_queue(self) -> list[int]:
        processed: list[int] = []
        for _ in range(100):
            job = SyncWorker(self.db).run_once(self.connector, connection_id=self.connection_id)
            if job is None:
                break
            processed.append(job.id)
            if job.status == "failed":
                self._retry_failed_job(job)
        return processed

    def _retry_failed_job(self, job: SyncJob) -> None:
        attempts = self._retry_counts.get(job.id, 0)
        if attempts >= self.max_retries:
            return
        failed_items = self.db.scalars(select(SyncItem).where(SyncItem.job_id == job.id, SyncItem.status == "failed")).all()
        if not failed_items:
            return
        for item in failed_items:
            item.status = "pending"
            item.processed_at = None
            item.error = None
        self._retry_counts[job.id] = attempts + 1
        job.status = "queued"
        job.error = None
        job.finished_at = None
        job.failed = 0
        self.db.commit()

    def status(self):
        return {"connection_id": self.connection_id, "interval_seconds": self.interval_seconds,
                "page_size": self.page_size, "max_retries": self.max_retries,
                "last_run_at": self.last_run_at, "last_error": self.last_error, "last_result": self.last_result}
