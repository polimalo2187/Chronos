from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.db.mongo import get_db

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    # PORTADA WEB (HTML directo, sin Jinja2)
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Chronos</title>
        <style>
          body{font-family:Arial,Helvetica,sans-serif;background:#0b1220;color:#e8eefc;margin:0}
          .wrap{max-width:900px;margin:0 auto;padding:48px 20px}
          .card{background:#111a2e;border:1px solid #1f2a44;border-radius:16px;padding:22px}
          .tag{display:inline-block;padding:6px 10px;border-radius:999px;background:#172548;border:1px solid #233257;color:#a8c1ff;font-size:12px}
          h1{margin:14px 0 6px 0;font-size:28px}
          p{margin:0;color:#b9c7e6}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="card">
            <span class="tag">Chronos</span>
            <h1>Chronos Web ✅</h1>
            <p>La API está viva y la portada HTML está funcionando.</p>
          </div>
        </div>
      </body>
    </html>
    """


@router.get("/health")
async def health():
    db = get_db()
    await db.command("ping")
    return {"ok": True}
