from fastapi import APIRouter

# Core routes
from app.api.routes import health, auth, users, telegram, admin, referrals

api_router = APIRouter()

# Health
api_router.include_router(health.router, tags=["health"])

# Auth
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Users
api_router.include_router(users.router, tags=["users"])

# Telegram linking
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])

# Admin
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Referrals (public landing)
api_router.include_router(referrals.router, tags=["referrals"])
