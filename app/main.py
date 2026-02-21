from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.db.mongo import ensure_indexes, get_db
from app.core.config import settings
from app.services.users import create_user
from pymongo.errors import DuplicateKeyError

import os

app = FastAPI(title="Chronos API", version="0.1.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# -----------------------
# UI (sin dependencias)
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Archivos estáticos (CSS/JS)
app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)

@app.get("/", include_in_schema=False)
async def web_index():
    """UI principal.

    Por defecto servimos el layout tipo app (sidebar + router).
    Si necesitas ver la portada web anterior: /web
    """
    app_file = os.path.join(WEB_DIR, "app_layout.html")
    if os.path.exists(app_file):
        return FileResponse(app_file)
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.get("/web", include_in_schema=False)
async def web_legacy():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

    # Bootstrap admin opcional (si configuras ADMIN_EMAIL + ADMIN_PASSWORD)
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
                    {"$set": {"plan": "premium", "plan_expires_at": None, "status": "active"}},
                )
        except DuplicateKeyError:
            pass
        except Exception:
            # Nunca tumbar el backend por bootstrap
            pass
