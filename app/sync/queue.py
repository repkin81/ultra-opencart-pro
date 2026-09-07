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
        job = self.db.scalar(
            select(SyncJob)
            .where(SyncJob.status == "queued")
            .order_by(SyncJob.id)
        )
        if job:
            job.status = "running"
            self.db.commit()
            self.db.refresh(job)
        return job

    def pending_items(self, job_id: int) -> list[SyncItem]:
        return list(self.db.scalars(
            select(SyncItem)
            .where(SyncItem.job_id == job_id, SyncItem.status == "pending")
            .order_by(SyncItem.id)
        ).all())
