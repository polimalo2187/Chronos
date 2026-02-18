from fastapi import APIRouter
from app.api.routes import health, auth, users, telegram, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
