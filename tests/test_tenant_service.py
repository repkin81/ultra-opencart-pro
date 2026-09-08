from app.database import SessionLocal
from app.tenants.models import Tenant
from app.tenants.schemas import TenantCreate
from app.tenants.service import TenantService


def test_tenant_service_creates_isolated_tenant():
    db = SessionLocal()
    slug = "test-isolated-tenant"
    try:
        existing = db.query(Tenant).filter(Tenant.slug == slug).first()
        if existing:
            db.delete(existing)
            db.commit()

        tenant = TenantService(db).create(
            TenantCreate(name="Test Isolated Tenant", slug=slug)
        )
        assert tenant.id is not None
        assert tenant.slug == slug
        assert tenant.is_active is True
        assert tenant.max_connections == 10
    finally:
        created = db.query(Tenant).filter(Tenant.slug == slug).first()
        if created:
            db.delete(created)
            db.commit()
        db.close()
