from fastapi import APIRouter

# Core routes
from app.api.routes import health, auth, users, telegram, admin

# Referral systems
from app.api.routes import referrals
from app.api.routes import referral   # ← ESTE FALTABA

api_router = APIRouter()

# ===== CORE =====
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(telegram.router)
api_router.include_router(admin.router)

# ===== REFERRALS =====
api_router.include_router(referrals.router)
api_router.include_router(referral.router)   # ← AQUI SE ACTIVA /referral/my-code
