from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.sync.schemas import SyncBatchIn, SyncJobOut, SyncPushOut
from app.sync.service import SyncService
from app.sync.worker import SyncWorker

router = APIRouter(prefix="/sync", tags=["Sync Core"])


@router.post("/push", response_model=SyncPushOut)
def push(
    batch: SyncBatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job, accepted, skipped = SyncService(db).enqueue(batch, current_user.id)
    return SyncPushOut(job_id=job.id, accepted=accepted, skipped=skipped)


@router.post("/jobs/{job_id}/run", response_model=SyncJobOut)
def run_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return SyncService(db).process(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/worker/run-once", response_model=SyncJobOut | None)
def worker_run_once(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return SyncWorker(db).run_once()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/worker/drain", response_model=list[SyncJobOut])
def worker_drain(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    try:
        return SyncWorker(db).drain(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs/{job_id}", response_model=SyncJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = SyncService(db).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")
    return job
