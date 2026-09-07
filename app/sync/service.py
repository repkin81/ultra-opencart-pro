import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sync.models import SyncItem, SyncJob, SyncMapping
from app.sync.schemas import SyncBatchIn, SyncItemIn


def canonical_checksum(payload: dict | None) -> str:
    raw = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, batch: SyncBatchIn, user_id: int | None = None) -> tuple[SyncJob, int, int]:
        job = SyncJob(direction=batch.direction, status="queued", requested_by=user_id, total=len(batch.items))
        self.db.add(job)
        self.db.flush()

        accepted = skipped = 0
        for item in batch.items:
            checksum = canonical_checksum(item.payload)
            mapping = self.db.scalar(
                select(SyncMapping).where(
                    SyncMapping.entity_type == item.entity_type,
                    SyncMapping.external_id == item.external_id,
                )
            )
            if mapping and mapping.checksum == checksum and item.operation == "upsert":
                skipped += 1
                continue
            self.db.add(SyncItem(
                job_id=job.id,
                entity_type=item.entity_type,
                external_id=item.external_id,
                operation=item.operation,
                payload=json.dumps(item.payload or {}, ensure_ascii=False),
                checksum=checksum,
            ))
            accepted += 1
        self.db.commit()
        self.db.refresh(job)
        return job, accepted, skipped

    def process(self, job_id: int) -> SyncJob:
        job = self.db.get(SyncJob, job_id)
        if not job:
            raise ValueError("Sync job not found")
        if job.status == "completed":
            return job

        job.status = "running"
        job.started_at = utcnow()
        self.db.commit()

        try:
            items = self.db.scalars(select(SyncItem).where(SyncItem.job_id == job.id).order_by(SyncItem.id)).all()
            for item in items:
                try:
                    if item.operation == "delete":
                        mapping = self.db.scalar(select(SyncMapping).where(
                            SyncMapping.entity_type == item.entity_type,
                            SyncMapping.external_id == item.external_id,
                        ))
                        if mapping:
                            self.db.delete(mapping)
                    else:
                        payload = json.loads(item.payload or "{}")
                        mapping = self.db.scalar(select(SyncMapping).where(
                            SyncMapping.entity_type == item.entity_type,
                            SyncMapping.external_id == item.external_id,
                        ))
                        if mapping is None:
                            mapping = SyncMapping(entity_type=item.entity_type, external_id=item.external_id, core_id=item.external_id)
                            self.db.add(mapping)
                        mapping.checksum = item.checksum or canonical_checksum(payload)
                    item.status = "success"
                    item.processed_at = utcnow()
                    job.succeeded += 1
                except Exception as exc:
                    item.status = "failed"
                    item.error = str(exc)
                    item.processed_at = utcnow()
                    job.failed += 1
                job.processed += 1
                self.db.commit()

            job.status = "failed" if job.failed else "completed"
            job.finished_at = utcnow()
            self.db.commit()
            self.db.refresh(job)
            return job
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = utcnow()
            self.db.commit()
            raise

    def get(self, job_id: int) -> SyncJob | None:
        return self.db.get(SyncJob, job_id)
