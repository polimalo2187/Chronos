from fastapi import APIRouter

from app.api.routes import health, auth, users, admin, referral

api_router = APIRouter()

# Core routes
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)

# Admin routes
api_router.include_router(admin.router)

# Referral routes
api_router.include_router(referral.router)
