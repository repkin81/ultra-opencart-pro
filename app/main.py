from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.deps import get_current_user
from app.auth.router import router as auth_router
from app.auth.schemas import UserOut
from app.config import get_settings
from app.core import init_database
from app.models.user import User
from app.opencart.router import router as opencart_router
from app.sync.connection_router import router as connection_router
from app.sync.connector_router import router as connector_router
from app.sync.router import router as sync_router
from app.sync.scheduler_manager import scheduler_manager
from app.sync.scheduler_router import router as scheduler_router
from app.sync.webhook_router import router as webhook_router
from app.tenants.router import router as tenants_router

settings = get_settings()
init_database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sync_scheduler_enabled:
        scheduler_manager.start()
    yield
    if scheduler_manager.running:
        scheduler_manager.stop()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(auth_router)
app.include_router(opencart_router)
app.include_router(sync_router)
app.include_router(connector_router)
app.include_router(connection_router)
app.include_router(scheduler_router)
app.include_router(webhook_router)
app.include_router(tenants_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "scheduler": scheduler_manager.running}


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user
