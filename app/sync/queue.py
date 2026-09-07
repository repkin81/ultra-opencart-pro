from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sync.models import SyncItem, SyncJob


class SyncQueue:
    """Database-backed queue for durable Sync Core jobs."""

    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, job: SyncJob) -> None:
        if job.status == "pending":
            job.status = "queued"
        self.db.add(job)
        self.db.commit()

    def next_job(self) -> SyncJob | None:
        # The worker selects a queued job; SyncService performs the actual
        # running transition. Scheduler-level locking prevents duplicate
        # execution in the standalone worker process.
        return self.db.scalar(
            select(SyncJob)
            .where(SyncJob.status == "queued")
            .order_by(SyncJob.id)
        )

    def pending_items(self, job_id: int) -> list[SyncItem]:
        return list(self.db.scalars(
            select(SyncItem)
            .where(SyncItem.job_id == job_id, SyncItem.status == "pending")
            .order_by(SyncItem.id)
        ).all())
