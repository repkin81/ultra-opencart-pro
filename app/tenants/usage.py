from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.sync.connection_models import OpenCartConnection
from app.sync.models import SyncJob, SyncItem
from app.models.user import User
from app.tenants.models import Tenant


def tenant_usage(db: Session, tenant: Tenant) -> dict[str, int]:
    connections = db.scalar(select(func.count()).select_from(OpenCartConnection).where(OpenCartConnection.tenant_id == tenant.id)) or 0
    users = db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id)) or 0
    jobs = db.scalar(select(func.count()).select_from(SyncJob).where(SyncJob.tenant_id == tenant.id)) or 0
    pending_items = db.scalar(
        select(func.count()).select_from(SyncItem).where(
            SyncItem.tenant_id == tenant.id,
            SyncItem.status.in_(["pending", "running"]),
        )
    ) or 0
    return {
        "users": int(users),
        "connections": int(connections),
        "sync_jobs": int(jobs),
        "pending_sync_items": int(pending_items),
    }
