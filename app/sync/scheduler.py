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
    """Automatic single-process scheduler for OpenCart <-> Core synchronization."""

    _lock = threading.Lock()

    def __init__(
        self,
        db: Session,
        connector: OpenCartConnector,
        interval_seconds: int = 60,
        page_size: int = 100,
        max_retries: int = 3,
    ):
        self.db = db
        self.connector = connector
        self.interval_seconds = max(5, interval_seconds)
        self.page_size = max(1, min(page_size, 1000))
        self.max_retries = max(0, max_retries)
        self.last_run_at: datetime | None = None
        self.last_error: str | None = None
        self.last_result: dict[str, Any] = {}
        self._retry_counts: dict[int, int] = {}

    def run_cycle(self) -> dict[str, Any]:
        if not self._lock.acquire(blocking=False):
            return {"status": "locked", "message": "Another scheduler cycle is already running"}

        started = utcnow()
        try:
            self.last_run_at = started
            self.last_error = None
            pulled = {"product": self._pull_all("product"), "category": self._pull_all("category")}
            processed = self._drain_queue()
            result = {
                "status": "ok",
                "started_at": started.isoformat(),
                "finished_at": utcnow().isoformat(),
                "pulled": pulled,
                "processed_jobs": processed,
            }
            self.last_result = result
            return result
        except Exception as exc:
            self.db.rollback()
            self.last_error = str(exc)
            logger.exception("Sync scheduler cycle failed")
            result = {"status": "error", "started_at": started.isoformat(), "finished_at": utcnow().isoformat(), "error": str(exc)}
            self.last_result = result
            return result
        finally:
            self._lock.release()

    def run_forever(self) -> None:
        logger.info("Sync scheduler started; interval=%ss", self.interval_seconds)
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
                SyncService(self.db).enqueue(SyncBatchIn(direction="opencart_to_core", items=items))
                total += len(items)

            if len(rows) < self.page_size:
                break
            page += 1
        return total

    def _drain_queue(self) -> list[int]:
        processed: list[int] = []
        for _ in range(100):
            job = SyncWorker(self.db).run_once(self.connector)
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

        failed_items = self.db.scalars(
            select(SyncItem).where(SyncItem.job_id == job.id, SyncItem.status == "failed")
        ).all()
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
        logger.warning("Sync job %s requeued for retry %s/%s", job.id, attempts + 1, self.max_retries)

    def status(self) -> dict[str, Any]:
        return {
            "running": self._lock.locked(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_error": self.last_error,
            "last_result": self.last_result,
            "interval_seconds": self.interval_seconds,
            "page_size": self.page_size,
            "max_retries": self.max_retries,
        }
