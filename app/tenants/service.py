from sqlalchemy import select
from sqlalchemy.orm import Session

from app.tenants.models import Tenant
from app.tenants.schemas import TenantCreate, TenantUpdate


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Tenant]:
        return list(self.db.scalars(select(Tenant).order_by(Tenant.id)).all())

    def get(self, tenant_id: int) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def create(self, data: TenantCreate) -> Tenant:
        if self.db.scalar(select(Tenant).where(Tenant.slug == data.slug)):
            raise ValueError("Tenant slug already exists")
        if self.db.scalar(select(Tenant).where(Tenant.name == data.name)):
            raise ValueError("Tenant name already exists")
        tenant = Tenant(**data.model_dump())
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def update(self, tenant: Tenant, data: TenantUpdate) -> Tenant:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(tenant, key, value)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def delete(self, tenant: Tenant) -> None:
        self.db.delete(tenant)
        self.db.commit()
