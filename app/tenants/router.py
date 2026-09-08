from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.tenants.context import get_current_tenant
from app.tenants.models import Tenant
from app.tenants.schemas import TenantCreate, TenantOut, TenantUpdate
from app.tenants.service import TenantService
from app.tenants.usage import tenant_usage

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


def _service(db: Session) -> TenantService:
    return TenantService(db)


@router.get("", response_model=list[TenantOut])
def list_tenants(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).list()


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(data: TenantCreate, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return _service(db).create(data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/current", response_model=TenantOut)
def current_tenant(tenant: Tenant = Depends(get_current_tenant)):
    return tenant


@router.get("/current/usage")
def current_tenant_usage(tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    usage = tenant_usage(db, tenant)
    return {
        **usage,
        "limits": {
            "users": tenant.max_users,
            "connections": tenant.max_connections,
            "api_keys": tenant.max_api_keys,
            "events_per_day": tenant.max_events_per_day,
        },
    }


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = _service(db).get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(tenant_id: int, data: TenantUpdate, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = _service(db)
    tenant = service.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return service.update(tenant, data)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(tenant_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = _service(db)
    tenant = service.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    service.delete(tenant)
