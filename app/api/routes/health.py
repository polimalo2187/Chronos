from fastapi import APIRouter

from app.db.mongo import get_db

router = APIRouter()


@router.get("/health")
async def health():
    """Healthcheck usado por Railway/monitoring."""
    db = get_db()
    await db.command("ping")
    return {"ok": True}
