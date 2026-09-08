from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.tenants.models import Tenant


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tenant:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    tenant = db.get(Tenant, current_user.tenant_id)
    if tenant is None or not tenant.is_active or tenant.status != "active":
        raise HTTPException(status_code=403, detail="Tenant is inactive or unavailable")
    return tenant
