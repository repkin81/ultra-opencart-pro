from fastapi import Depends, FastAPI

from app.api.deps import get_current_user
from app.auth.router import router as auth_router
from app.auth.schemas import UserOut
from app.config import get_settings
from app.core import init_database
from app.models.user import User
from app.opencart.router import router as opencart_router
from app.sync.router import router as sync_router

settings = get_settings()
init_database()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(auth_router)
app.include_router(opencart_router)
app.include_router(sync_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user
