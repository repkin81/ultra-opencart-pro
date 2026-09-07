from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.sync.connector import OpenCartConnector
from app.sync.connector_schemas import ConnectorConfig
from app.sync.scheduler import SyncScheduler

router = APIRouter(prefix="/sync/scheduler", tags=["Sync Scheduler"])


def build_scheduler(db: Session, config: ConnectorConfig) -> SyncScheduler:
    settings = get_settings()
    return SyncScheduler(
        db,
        OpenCartConnector(config.base_url, config.api_key, config.timeout),
        interval_seconds=settings.sync_interval_seconds,
        page_size=settings.sync_page_size,
        max_retries=settings.sync_max_retries,
    )


@router.post("/run")
def run_scheduler(
    config: ConnectorConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = build_scheduler(db, config).run_cycle()
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("error", "Scheduler failed"))
    return result


@router.post("/heartbeat")
def scheduler_heartbeat(
    config: ConnectorConfig,
    current_user: User = Depends(get_current_user),
):
    connector = OpenCartConnector(config.base_url, config.api_key, config.timeout)
    try:
        return connector.heartbeat()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
