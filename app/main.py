from fastapi import Depends, FastAPI

from app.api.deps import get_current_user
from app.auth.router import router as auth_router
from app.auth.schemas import UserOut
from app.config import get_settings
from app.database import Base, engine
from app.models.user import User

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(auth_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user
