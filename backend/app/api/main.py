from fastapi import APIRouter

from app.api.routes import auth, portfolio, private, upload, users, utils
from app.api.routes import settings as settings_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(settings_router.router)
api_router.include_router(upload.router)
api_router.include_router(portfolio.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
