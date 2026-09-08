from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.sync.connection_models import OpenCartConnection
from app.sync.models import SyncItem, SyncJob, SyncMapping
from app.tenants.models import Tenant


def ensure_default_tenant() -> int:
    """Keep existing single-tenant installations usable during the migration."""
    db: Session = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "default"))
        if tenant is None:
            tenant = Tenant(name="Default Organization", slug="default")
            db.add(tenant)
            db.flush()

        assignments = [
            (User, User.tenant_id),
            (OpenCartConnection, OpenCartConnection.tenant_id),
            (SyncJob, SyncJob.tenant_id),
            (SyncItem, SyncItem.tenant_id),
            (SyncMapping, SyncMapping.tenant_id),
        ]
        for model, column in assignments:
            db.execute(update(model).where(column.is_(None)).values(tenant_id=tenant.id))
        db.commit()
        return tenant.id
    finally:
        db.close()
