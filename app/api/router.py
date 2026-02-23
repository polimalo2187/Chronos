from fastapi import APIRouter
from app.api.routes import health, auth, users, telegram, admin

# Referrals (opcional): si el módulo aún no existe, NO debe tumbar la app en startup
try:
    from app.api.routes import referrals  # debe exponer `router`
except Exception:
    referrals = None

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# /referrals/*
if referrals is not None:
    api_router.include_router(referrals.router, prefix="/referrals", tags=["referrals"])
