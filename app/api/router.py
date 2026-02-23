from fastapi import APIRouter

from app.api.routes import health, auth, users, telegram, admin, referrals

api_router = APIRouter()

Core routes

api_router.include_router(health.router, tags=["health"]) api_router.include_router(auth.router, prefix="/auth", tags=["auth"]) api_router.include_router(users.router, prefix="/users", tags=["users"]) api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])

Admin panel

api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

Referrals system

api_router.include_router(referrals.router, prefix="/referrals", tags=["referrals"])
