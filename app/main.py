from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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

# --- Web UI (sin Jinja2) ---
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

# Sirve /web/app.css, /web/app.js, etc.
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")

@app.get("/")
async def web_root():
    # UI tipo app (mismo servicio)
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"name": "Chronos API", "status": "ok"}

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

    # bootstrap admin opcional (no tumbar backend)
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
