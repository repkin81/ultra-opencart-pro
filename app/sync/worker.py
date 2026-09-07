from sqlalchemy import select
from sqlalchemy.orm import Session

from app.sync.connector import OpenCartConnector
from app.sync.models import SyncJob
from app.sync.queue import SyncQueue
from app.sync.service import SyncService


class SyncWorker:
    def __init__(self, db: Session):
        self.db = db

    def run_once(self, connector: OpenCartConnector | None = None, connection_id: int | None = None) -> SyncJob | None:
        queue = SyncQueue(self.db)
        job = queue.next_job(connection_id=connection_id)
        if job is None:
            return None
        try:
            return SyncService(self.db).process(job.id, connector)
        except Exception:
            self.db.rollback()
            failed = self.db.get(SyncJob, job.id)
            if failed is not None:
                failed.status = "failed"
                self.db.commit()
            raise

    def drain(self, connector: OpenCartConnector | None = None, limit: int = 10, connection_id: int | None = None) -> list[SyncJob]:
        results: list[SyncJob] = []
        for _ in range(limit):
            job = self.run_once(connector, connection_id=connection_id)
            if job is None:
                break
            results.append(job)
        return results
