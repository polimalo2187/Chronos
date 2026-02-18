from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.mongo import ensure_indexes, get_db
from app.core.config import settings
from app.services.users import create_user
from pymongo.errors import DuplicateKeyError

app = FastAPI(title="Chronos API", version="0.1.0")

# CORS (ajusta dominios cuando tengas frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    await ensure_indexes()
    # optional bootstrap admin
    if settings.admin_email and settings.admin_password:
        db = get_db()
        existing = await db.users.find_one({"email": settings.admin_email.lower()})
        if not existing:
            try:
                await create_user(settings.admin_email, settings.admin_password, is_admin=True)
                # Make admin premium by default
                await db.users.update_one(
                    {"email": settings.admin_email.lower()},
                    {"$set": {"plan": "premium", "plan_expires_at": None}}
                )
            except DuplicateKeyError:
                pass
