from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.sync.connection_models import OpenCartConnection, utcnow
from app.sync.connector import OpenCartConnector
from app.sync.connector_schemas import ConnectorConfig
from app.sync.scheduler import SyncScheduler

router = APIRouter(prefix="/sync/scheduler", tags=["Sync Scheduler"])


def build_scheduler(db: Session, config: ConnectorConfig, connection_id: int | None = None) -> SyncScheduler:
    settings = get_settings()
    return SyncScheduler(db, OpenCartConnector(config.base_url, config.api_key, config.timeout),
                         connection_id=connection_id, interval_seconds=settings.sync_interval_seconds,
                         page_size=settings.sync_page_size, max_retries=settings.sync_max_retries)


@router.post("/run")
def run_scheduler(config: ConnectorConfig, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = build_scheduler(db, config).run_cycle()
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("error", "Scheduler failed"))
    return result


@router.post("/connections/{connection_id}/run")
def run_connection_scheduler(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    if not connection.enabled:
        raise HTTPException(status_code=409, detail="OpenCart connection is disabled")
    scheduler = SyncScheduler(db, OpenCartConnector(connection.base_url, connection.api_key, connection.timeout),
                              connection_id=connection.id, interval_seconds=connection.interval_seconds,
                              page_size=connection.page_size, max_retries=get_settings().sync_max_retries)
    connection.last_run_at = utcnow()
    result = scheduler.run_cycle()
    if result.get("status") == "ok":
        connection.last_success_at = utcnow()
        connection.last_error = None
    else:
        connection.last_error = result.get("error")
    db.commit()
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("error", "Scheduler failed"))
    return result


@router.post("/connections/run-enabled")
def run_enabled_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = get_settings()
    connections = db.scalars(select(OpenCartConnection).where(OpenCartConnection.enabled.is_(True)).order_by(OpenCartConnection.id)).all()
    results = []
    for connection in connections:
        scheduler = SyncScheduler(db, OpenCartConnector(connection.base_url, connection.api_key, connection.timeout),
                                   connection_id=connection.id, interval_seconds=connection.interval_seconds,
                                   page_size=connection.page_size, max_retries=settings.sync_max_retries)
        connection.last_run_at = utcnow()
        result = scheduler.run_cycle()
        if result.get("status") == "ok":
            connection.last_success_at = utcnow()
            connection.last_error = None
        else:
            connection.last_error = result.get("error")
        results.append(result)
        db.commit()
    return {"count": len(results), "results": results}


@router.post("/heartbeat")
def scheduler_heartbeat(config: ConnectorConfig, current_user: User = Depends(get_current_user)):
    connector = OpenCartConnector(config.base_url, config.api_key, config.timeout)
    try:
        return connector.heartbeat()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connections/{connection_id}/heartbeat")
def connection_heartbeat(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    try:
        response = OpenCartConnector(connection.base_url, connection.api_key, connection.timeout).heartbeat()
        connection.last_success_at = utcnow()
        connection.last_error = None
        db.commit()
        return {"connection_id": connection.id, "ok": True, "response": response}
    except Exception as exc:
        connection.last_error = str(exc)
        db.commit()
        return {"connection_id": connection.id, "ok": False, "error": str(exc)}
