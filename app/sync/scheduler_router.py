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
from app.sync.scheduler_manager import scheduler_manager

router = APIRouter(prefix="/sync/scheduler", tags=["Sync Scheduler"])


def build_scheduler(db: Session, config: ConnectorConfig, connection_id: int | None = None) -> SyncScheduler:
    settings = get_settings()
    return SyncScheduler(
        db,
        OpenCartConnector(config.base_url, config.api_key, config.timeout),
        connection_id=connection_id,
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
        raise HTTPException(status_code=502, detail=result)
    return result


@router.post("/connections/{connection_id}/run")
def run_connection_scheduler(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    if not connection.enabled:
        raise HTTPException(status_code=409, detail="OpenCart connection is disabled")
    scheduler = SyncScheduler(
        db,
        OpenCartConnector(connection.base_url, connection.api_key, connection.timeout),
        connection_id=connection.id,
        interval_seconds=connection.interval_seconds,
        page_size=connection.page_size,
        max_retries=get_settings().sync_max_retries,
    )
    connection.last_run_at = utcnow()
    result = scheduler.run_cycle()
    if result.get("status") == "ok":
        connection.last_success_at = utcnow()
        connection.last_error = None
    else:
        connection.last_error = str(result.get("error") or scheduler.last_error or "Sync failed")
    db.commit()
    return result


@router.post("/connections/run-enabled")
def run_enabled_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connections = db.scalars(
        select(OpenCartConnection)
        .where(OpenCartConnection.enabled.is_(True))
        .order_by(OpenCartConnection.id)
    ).all()
    results = []
    for connection in connections:
        scheduler = SyncScheduler(
            db,
            OpenCartConnector(connection.base_url, connection.api_key, connection.timeout),
            connection_id=connection.id,
            interval_seconds=connection.interval_seconds,
            page_size=connection.page_size,
            max_retries=get_settings().sync_max_retries,
        )
        connection.last_run_at = utcnow()
        try:
            result = scheduler.run_cycle()
            if result.get("status") == "ok":
                connection.last_success_at = utcnow()
                connection.last_error = None
            else:
                connection.last_error = str(result.get("error") or scheduler.last_error or "Sync failed")
            results.append(result)
            db.commit()
        except Exception as exc:
            db.rollback()
            results.append({"connection_id": connection.id, "status": "error", "error": str(exc)})
    return {"status": "ok", "connections": results}


@router.post("/heartbeat")
def scheduler_heartbeat(
    config: ConnectorConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheduler = build_scheduler(db, config)
    return scheduler.connector.heartbeat()


@router.post("/connections/{connection_id}/heartbeat")
def connection_heartbeat(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    return OpenCartConnector(connection.base_url, connection.api_key, connection.timeout).heartbeat()


@router.post("/manager/start")
def start_manager(current_user: User = Depends(get_current_user)):
    started = scheduler_manager.start()
    return {"status": "started" if started else "already_running", **scheduler_manager.status()}


@router.post("/manager/stop")
def stop_manager(current_user: User = Depends(get_current_user)):
    stopped = scheduler_manager.stop()
    return {"status": "stopped" if stopped else "not_running", **scheduler_manager.status()}


@router.get("/manager/status")
def manager_status(current_user: User = Depends(get_current_user)):
    return scheduler_manager.status()
