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

# API routes (/health, /auth/*, /me, /telegram/*, /admin/*, etc.)
app.include_router(api_router)


# -----------------------
# Helpers (links)
# -----------------------
def _safe_whatsapp_link() -> str:
    wa = (getattr(settings, "whatsapp_contact", "") or "").strip()
    if not wa:
        return ""
    if wa.startswith("http://") or wa.startswith("https://"):
        return wa
    digits = "".join([c for c in wa if c.isdigit()])
    return f"https://wa.me/{digits}" if digits else ""


def _safe_telegram_bot_link() -> str:
    tg_user = (getattr(settings, "telegram_bot_username", "") or "").strip().lstrip("@")
    return f"https://t.me/{tg_user}" if tg_user else ""


# -----------------------
# Web landing (NO jinja2)
# -----------------------
@app.get("/", response_class=HTMLResponse)
async def landing():
    wa = _safe_whatsapp_link()
    tg = _safe_telegram_bot_link()

    # Ajusta estos destinos cuando tengas frontend real (por ahora son anchors y docs)
    login_href = "/docs#/auth/login_auth_login_post"
    register_href = "/docs#/auth/register_auth_register_post"
    docs_href = "/docs"

    wa_btn = (
        f'<a class="btn btn-primary" href="{wa}" target="_blank" rel="noopener">Contratar por WhatsApp</a>'
        if wa
        else '<a class="btn btn-disabled" href="#" aria-disabled="true">WhatsApp no configurado</a>'
    )
    tg_btn = (
        f'<a class="btn btn-ghost" href="{tg}" target="_blank" rel="noopener">Vincular Telegram</a>'
        if tg
        else '<a class="btn btn-disabled" href="#" aria-disabled="true">Telegram no configurado</a>'
    )

    html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Chronos</title>
  <style>
    :root {{
      --bg0: #070A12;
      --bg1: #0B1224;
      --card: rgba(255,255,255,.06);
      --card2: rgba(255,255,255,.08);
      --line: rgba(255,255,255,.12);
      --text: rgba(255,255,255,.92);
      --muted: rgba(255,255,255,.70);
      --muted2: rgba(255,255,255,.55);
      --accent: #6EE7FF;
      --accent2: #8B5CF6;
      --ok: #34D399;
      --warn: #FBBF24;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji","Segoe UI Emoji";
      color: var(--text);
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(110,231,255,.18), transparent 55%),
        radial-gradient(900px 700px at 80% 30%, rgba(139,92,246,.16), transparent 55%),
        radial-gradient(900px 700px at 50% 100%, rgba(52,211,153,.10), transparent 60%),
        linear-gradient(180deg, var(--bg0), var(--bg1));
      min-height: 100vh;
      overflow-x: hidden;
    }}
    .grid {{
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(to right, rgba(255,255,255,.06) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,.06) 1px, transparent 1px);
      background-size: 64px 64px;
      mask-image: radial-gradient(ellipse at 50% 20%, rgba(0,0,0,1), rgba(0,0,0,0) 65%);
      pointer-events: none;
      opacity: .35;
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px 18px 56px;
    }}
    .top {{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap: 14px;
    }}
    .brand {{
      display:flex;
      align-items:center;
      gap: 10px;
    }}
    .logo {{
      width: 38px; height: 38px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(110,231,255,.95), rgba(139,92,246,.95));
      box-shadow: 0 18px 50px rgba(110,231,255,.14), 0 18px 50px rgba(139,92,246,.12);
    }}
    .brand h1 {{
      font-size: 18px;
      margin: 0;
      letter-spacing: .6px;
      font-weight: 800;
    }}
    .pill {{
      padding: 7px 10px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.05);
      border-radius: 999px;
      color: var(--muted);
      font-size: 12px;
      display:flex;
      gap: 8px;
      align-items:center;
      white-space: nowrap;
    }}
    .dot {{
      width: 8px; height: 8px; border-radius: 999px;
      background: var(--ok);
      box-shadow: 0 0 0 6px rgba(52,211,153,.12);
    }}
    .hero {{
      margin-top: 30px;
      display:grid;
      grid-template-columns: 1.15fr .85fr;
      gap: 18px;
      align-items: stretch;
    }}
    @media (max-width: 900px) {{
      .hero {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 22px;
      padding: 22px;
      backdrop-filter: blur(10px);
      box-shadow: 0 18px 60px rgba(0,0,0,.35);
    }}
    .headline {{
      font-size: 44px;
      line-height: 1.05;
      margin: 0 0 12px;
      letter-spacing: -0.6px;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
      max-width: 62ch;
    }}
    .cta {{
      margin-top: 18px;
      display:flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .btn {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap: 8px;
      border-radius: 14px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      text-decoration: none;
      color: var(--text);
      background: rgba(255,255,255,.06);
      font-weight: 650;
      font-size: 14px;
      transition: transform .12s ease, background .12s ease, border-color .12s ease;
    }}
    .btn:hover {{ transform: translateY(-1px); background: rgba(255,255,255,.09); border-color: rgba(255,255,255,.18); }}
    .btn-primary {{
      border: 1px solid rgba(110,231,255,.35);
      background: linear-gradient(135deg, rgba(110,231,255,.18), rgba(139,92,246,.16));
    }}
    .btn-ghost {{
      border: 1px dashed rgba(255,255,255,.22);
      background: rgba(255,255,255,.04);
    }}
    .btn-disabled {{
      opacity: .55;
      pointer-events: none;
    }}
    .kpis {{
      margin-top: 18px;
      display:grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }}
    @media (max-width: 520px) {{
      .kpis {{ grid-template-columns: 1fr; }}
      .headline {{ font-size: 38px; }}
    }}
    .kpi {{
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.05);
      border-radius: 18px;
      padding: 14px;
    }}
    .kpi .t {{
      color: var(--muted2);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .kpi .v {{
      font-size: 16px;
      font-weight: 800;
      letter-spacing: .2px;
    }}
    .side h2 {{
      margin: 0 0 10px;
      font-size: 16px;
      color: rgba(255,255,255,.88);
    }}
    .list {{
      margin: 0;
      padding: 0;
      list-style: none;
      display:grid;
      gap: 10px;
    }}
    .item {{
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.05);
      border-radius: 16px;
      padding: 12px;
    }}
    .item .tt {{
      font-weight: 800;
      font-size: 13px;
      margin: 0 0 4px;
    }}
    .item .dd {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .foot {{
      margin-top: 16px;
      color: rgba(255,255,255,.52);
      font-size: 12px;
    }}
    code {{
      background: rgba(255,255,255,.07);
      padding: 2px 6px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.10);
    }}
  </style>
</head>
<body>
  <div class="grid"></div>
  <div class="wrap">
    <div class="top">
      <div class="brand">
        <div class="logo"></div>
        <h1>Chronos</h1>
      </div>
      <div class="pill">
        <span class="dot"></span>
        API viva · Portada HTML activa
      </div>
    </div>

    <div class="hero">
      <div class="card">
        <h2 class="headline">Señales con criterio.<br/>Interfaz con poder.</h2>
        <p class="sub">
          Chronos es una plataforma de señales con estética institucional-tecnológica: limpia, rápida y enfocada a decisión.
          Registro con <b>trial free 7 días</b>, y planes <b>Plus/Premium 30 días</b> activados manualmente por el administrador.
        </p>

        <div class="cta">
          <a class="btn btn-primary" href="{register_href}">Registro (API)</a>
          <a class="btn" href="{login_href}">Login (API)</a>
          <a class="btn btn-ghost" href="{docs_href}">Docs API</a>
          {wa_btn}
          {tg_btn}
        </div>

        <div class="kpis">
          <div class="kpi">
            <div class="t">Trial</div>
            <div class="v">Free · 7 días</div>
          </div>
          <div class="kpi">
            <div class="t">Planes</div>
            <div class="v">Plus / Premium · 30 días</div>
          </div>
          <div class="kpi">
            <div class="t">Acceso</div>
            <div class="v">Bloqueo al expirar</div>
          </div>
        </div>

        <div class="foot">
          Tip: tus endpoints siguen igual. Ejemplo: <code>/health</code>, <code>/docs</code>, <code>/openapi.json</code>
        </div>
      </div>

      <div class="card side">
        <h2>Roadmap visual (lo próximo)</h2>
        <ul class="list">
          <li class="item">
            <p class="tt">1) Portada real (UI)</p>
            <p class="dd">Esta portada ya es “real” sin dependencias extra. Luego pasamos a login/register web y panel admin.</p>
          </li>
          <li class="item">
            <p class="tt">2) Panel Admin</p>
            <p class="dd">Activar Plus/Premium por email o telegram_id · ban temporal/permanente · ver estado.</p>
          </li>
          <li class="item">
            <p class="tt">3) Scanner</p>
            <p class="dd">Proceso aparte. Publica top 3 señales por score, respetando acceso (Free/Plus/Premium).</p>
          </li>
        </ul>
        <div class="foot">
          Identidad visual: dark-glass + grid sutil + acentos cyan/violet (único y “institucional-tech”).
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(html)


# Opcional: ruta separada si quieres probar otra pantalla
@app.get("/panel", response_class=HTMLResponse)
async def panel_placeholder():
    return HTMLResponse(
        "<h2 style='font-family:system-ui;padding:20px'>Panel en construcción ✅</h2>"
        "<p style='font-family:system-ui;padding:0 20px'>Ahora la prioridad es terminar UI del panel admin con estética Chronos.</p>"
    )


# -----------------------
# Startup
# -----------------------
@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

    # Bootstrap admin opcional (no tumbar backend)
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
