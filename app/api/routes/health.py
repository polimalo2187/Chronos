from fastapi import APIRouter
from app.db.mongo import get_db

router = APIRouter()

# Endpoint informativo del API (NO interfiere con la portada web)
@router.get("/api")
async def root():
    return {"name": "Chronos API", "status": "ok"}

# Healthcheck real usado por Railway / monitoreo
@router.get("/health")
async def health():
    db = get_db()
    await db.command("ping")
    return {"ok": True}
