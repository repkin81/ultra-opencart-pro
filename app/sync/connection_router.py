from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.sync.connection_models import OpenCartConnection, utcnow
from app.sync.connection_schemas import ConnectionCreate, ConnectionOut, ConnectionTestOut, ConnectionUpdate
from app.sync.connector import OpenCartConnector

router = APIRouter(prefix="/sync/connections", tags=["Sync Connections"])


def _get_connection(db: Session, connection_id: int) -> OpenCartConnection:
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    return connection


def _out(connection: OpenCartConnection) -> ConnectionOut:
    return ConnectionOut(
        id=connection.id,
        name=connection.name,
        base_url=connection.base_url,
        timeout=connection.timeout,
        enabled=connection.enabled,
        interval_seconds=connection.interval_seconds,
        page_size=connection.page_size,
        has_api_key=bool(connection.api_key),
        last_run_at=connection.last_run_at,
        last_success_at=connection.last_success_at,
        last_error=connection.last_error,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.get("", response_model=list[ConnectionOut])
def list_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.scalars(select(OpenCartConnection).order_by(OpenCartConnection.id)).all()
    return [_out(row) for row in rows]


@router.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = OpenCartConnection(
        name=data.name,
        base_url=str(data.base_url).rstrip("/"),
        api_key=data.api_key,
        timeout=data.timeout,
        enabled=data.enabled,
        interval_seconds=data.interval_seconds,
        page_size=data.page_size,
    )
    db.add(connection)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Connection name already exists") from exc
    db.refresh(connection)
    return _out(connection)


@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _out(_get_connection(db, connection_id))


@router.patch("/{connection_id}", response_model=ConnectionOut)
def update_connection(
    connection_id: int,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = _get_connection(db, connection_id)
    values = data.model_dump(exclude_unset=True)
    if "base_url" in values and values["base_url"] is not None:
        values["base_url"] = str(values["base_url"]).rstrip("/")
    for key, value in values.items():
        setattr(connection, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Connection name already exists") from exc
    db.refresh(connection)
    return _out(connection)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    connection = _get_connection(db, connection_id)
    db.delete(connection)
    db.commit()


@router.post("/{connection_id}/test", response_model=ConnectionTestOut)
def test_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = _get_connection(db, connection_id)
    connector = OpenCartConnector(connection.base_url, connection.api_key, connection.timeout)
    connection.last_run_at = utcnow()
    try:
        response = connector.heartbeat()
        connection.last_success_at = utcnow()
        connection.last_error = None
        db.commit()
        return ConnectionTestOut(connection_id=connection.id, ok=True, response=response)
    except Exception as exc:
        connection.last_error = str(exc)
        db.commit()
        return ConnectionTestOut(connection_id=connection.id, ok=False, error=str(exc))
