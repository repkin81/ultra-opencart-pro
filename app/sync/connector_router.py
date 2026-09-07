from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.sync.connector import OpenCartConnector
from app.sync.connector_schemas import ConnectorConfig, PullRequest
from app.sync.puller import OpenCartPuller
from app.sync.schemas import SyncJobOut, SyncPushOut
from app.sync.service import SyncService

router = APIRouter(prefix="/sync/connector", tags=["OpenCart Connector"])


@router.post("/heartbeat")
def heartbeat(config: ConnectorConfig, current_user: User = Depends(get_current_user)):
    try:
        return {"ok": True, "data": OpenCartConnector(config.base_url, config.api_key, config.timeout).heartbeat()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/pull", response_model=SyncPushOut)
def pull(
    request: PullRequest,
    config: ConnectorConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        connector = OpenCartConnector(config.base_url, config.api_key, config.timeout)
        job, accepted, skipped = OpenCartPuller(connector, SyncService(db)).pull(
            request.entity_type, request.page, request.limit, current_user.id
        )
        return SyncPushOut(job_id=job.id, accepted=accepted, skipped=skipped)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/run", response_model=SyncJobOut)
def run_job(
    job_id: int,
    config: ConnectorConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        connector = OpenCartConnector(config.base_url, config.api_key, config.timeout)
        return SyncService(db).process(job_id, connector)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
