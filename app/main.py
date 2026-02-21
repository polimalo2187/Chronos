from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.router import api_router
from app.db.mongo import ensure_indexes, get_db
from app.core.config import settings
from app.services.users import create_user
from pymongo.errors import DuplicateKeyError


app = FastAPI(title="Chronos API", version="0.1.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _safe_whatsapp_link() -> str:
    wa = (getattr(settings, "whatsapp_contact", "") or "").strip()
    if not wa:
        return ""
    if wa.startswith("http"):
        return wa
    digits = "".join([c for c in wa if c.isdigit()])
    return f"https://wa.me/{digits}" if digits else ""


def _safe_telegram_link() -> str:
    tg_user = (getattr(settings, "telegram_bot_username", "") or "").strip().lstrip("@")
    return f"https://t.me/{tg_user}" if tg_user else ""


@app.get("/", response_class=HTMLResponse)
async def landing():
    return HTMLResponse("<h1>Chronos placeholder</h1>")


@app.get("/panel", response_class=HTMLResponse)
async def panel():
    return HTMLResponse("<h1>Panel placeholder</h1>")


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

    if settings.admin_email and settings.admin_password:
        admin_email = settings.admin_email.strip()
        admin_password = settings.admin_password.strip()

        try:
            db = get_db()
            existing = await db.users.find_one({"email": admin_email.lower()})
            if not existing:
                await create_user(admin_email, admin_password, is_admin=True)
                await db.users.update_one(
                    {"email": admin_email.lower()},
                    {"$set": {"plan": "premium", "plan_expires_at": None}}
                )
        except DuplicateKeyError:
            pass
        except Exception:
            pass
