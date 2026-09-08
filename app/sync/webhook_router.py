from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.sync.connection_models import OpenCartConnection
from app.sync.models import SyncItem
from app.sync.schemas import SyncBatchIn, SyncItemIn
from app.sync.service import SyncService
from app.sync.webhook_schemas import WebhookEventIn, WebhookEventOut

router = APIRouter(prefix="/sync/webhooks", tags=["Sync Webhooks"])


@router.post("/{connection_id}", response_model=WebhookEventOut, status_code=status.HTTP_202_ACCEPTED)
def receive_webhook(
    connection_id: int,
    event: WebhookEventIn,
    db: Session = Depends(get_db),
    x_sync_event_id: str | None = Header(default=None),
    x_sync_api_key: str | None = Header(default=None),
):
    connection = db.get(OpenCartConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="OpenCart connection not found")
    if not connection.enabled:
        raise HTTPException(status_code=409, detail="OpenCart connection is disabled")
    if not connection.api_key or x_sync_api_key != connection.api_key:
        raise HTTPException(status_code=401, detail="Invalid webhook credentials")

    event_id = x_sync_event_id or event.event_id or str(uuid4())
    existing = db.scalar(
        select(SyncItem).where(
            SyncItem.connection_id == connection_id,
            SyncItem.external_id == event.entity_id,
            SyncItem.entity_type == event.entity_type,
            SyncItem.checksum == event_id,
        )
    )
    if existing is not None:
        return WebhookEventOut(
            accepted=True, duplicate=True, event_id=event_id,
            event_type=event.event_type, connection_id=connection_id, queued=False,
        )

    operation = "delete" if event.event_type.endswith(".deleted") else "upsert"
    item = SyncItemIn(
        entity_type=event.entity_type,
        external_id=event.entity_id,
        operation=operation,
        payload=event.payload,
    )
    job = SyncService(db).enqueue(
        SyncBatchIn(direction="opencart_to_core", connection_id=connection_id, items=[item])
    )
    queued_item = db.scalar(select(SyncItem).where(SyncItem.job_id == job.id).order_by(SyncItem.id.desc()))
    if queued_item is not None:
        queued_item.checksum = event_id
        db.commit()

    return WebhookEventOut(
        accepted=True, duplicate=False, event_id=event_id,
        event_type=event.event_type, connection_id=connection_id, queued=True,
    )


@router.get("/health", tags=["Sync Webhooks"])
def webhook_health():
    return {"status": "ok"}
