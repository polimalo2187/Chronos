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


@app.get("/", response_class=HTMLResponse)
async def landing():
    """
    Portada estética (sin framework) para que ya veas la identidad visual de Chronos.
    No rompe la API: solo agrega una home bonita.
    """
    wa = (getattr(settings, "whatsapp_contact", "") or "").strip()
    if wa and not wa.startswith("http"):
        # si te pasan "+53..." o "5355..." lo convertimos a wa.me
        digits = "".join([c for c in wa if c.isdigit()])
        if digits:
            wa = f"https://wa.me/{digits}"

    tg_user = (getattr(settings, "telegram_bot_username", "") or "").strip().lstrip("@")
    tg_link = f"https://t.me/{tg_user}" if tg_user else ""

    # Rutas útiles
    docs_url = "/docs"
    health_url = "/health"

    html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Chronos • Señales MTF</title>
  <style>
    :root {{
      --bg0:#060812;
      --bg1:#090B18;
      --card: rgba(255,255,255,.06);
      --card2: rgba(255,255,255,.08);
      --line: rgba(255,255,255,.10);
      --txt: rgba(255,255,255,.92);
      --muted: rgba(255,255,255,.68);
      --accent: #7C5CFF;
      --accent2:#20D3FF;
      --ok:#4CFFB5;
      --warn:#FFC94A;
      --danger:#FF4D6D;
      --shadow: 0 20px 60px rgba(0,0,0,.45);
    }}
    *{{box-sizing:border-box}}
    html,body{{height:100%}}
    body {{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Helvetica Neue";
      color:var(--txt);
      background:
        radial-gradient(900px 600px at 15% 10%, rgba(124,92,255,.18), transparent 60%),
        radial-gradient(900px 600px at 85% 15%, rgba(32,211,255,.14), transparent 60%),
        radial-gradient(900px 600px at 70% 90%, rgba(76,255,181,.10), transparent 60%),
        linear-gradient(180deg, var(--bg0), var(--bg1));
      overflow-x:hidden;
    }}
    .grid {{
      position:fixed; inset:0;
      background-image:
        linear-gradient(to right, rgba(255,255,255,.04) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,.04) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: radial-gradient(circle at 50% 20%, black 35%, transparent 75%);
      pointer-events:none;
      opacity:.7;
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px 18px 64px;
      position:relative;
    }}
    header {{
      display:flex; align-items:center; justify-content:space-between;
      gap:12px;
      padding: 10px 6px 22px;
    }}
    .brand {{
      display:flex; align-items:center; gap:12px;
    }}
    .logo {{
      width:42px; height:42px;
      border-radius:14px;
      background:
        radial-gradient(18px 18px at 30% 30%, rgba(255,255,255,.35), transparent 60%),
        linear-gradient(135deg, rgba(124,92,255,.95), rgba(32,211,255,.85));
      box-shadow: 0 16px 40px rgba(124,92,255,.18);
      border:1px solid rgba(255,255,255,.16);
    }}
    .brand h1 {{
      margin:0;
      font-size: 16px;
      letter-spacing: .4px;
      font-weight: 700;
      line-height: 1.1;
    }}
    .brand small {{
      display:block;
      margin-top:2px;
      color: var(--muted);
      font-weight: 500;
      font-size: 12px;
      letter-spacing:.3px;
    }}
    .top-actions {{
      display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end;
    }}
    .btn {{
      display:inline-flex; align-items:center; justify-content:center;
      gap:10px;
      padding: 10px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,.06);
      border:1px solid rgba(255,255,255,.10);
      color: var(--txt);
      text-decoration:none;
      font-weight:600;
      font-size: 13px;
      transition: transform .12s ease, background .12s ease, border-color .12s ease;
      user-select:none;
    }}
    .btn:hover {{
      transform: translateY(-1px);
      background: rgba(255,255,255,.09);
      border-color: rgba(255,255,255,.16);
    }}
    .btn.primary {{
      background: linear-gradient(135deg, rgba(124,92,255,.95), rgba(32,211,255,.85));
      border-color: rgba(255,255,255,.20);
      box-shadow: 0 18px 50px rgba(124,92,255,.18);
    }}
    .btn.primary:hover {{ filter: brightness(1.04); }}
    .hero {{
      display:grid;
      grid-template-columns: 1.15fr .85fr;
      gap: 18px;
      margin-top: 8px;
    }}
    @media (max-width: 920px) {{
      .hero {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      overflow:hidden;
    }}
    .card.pad {{ padding: 18px; }}
    .headline {{
      padding: 22px 18px 16px;
      border-bottom:1px solid rgba(255,255,255,.08);
      background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,0));
    }}
    .kicker {{
      display:inline-flex;
      align-items:center;
      gap:8px;
      font-size:12px;
      color: var(--muted);
      letter-spacing:.4px;
    }}
    .dot {{
      width:8px; height:8px; border-radius:99px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      box-shadow: 0 0 0 6px rgba(124,92,255,.10);
    }}
    h2 {{
      margin: 10px 0 8px;
      font-size: 34px;
      line-height:1.08;
      letter-spacing:.2px;
    }}
    p {{
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.65;
    }}
    .chips {{
      display:flex; flex-wrap:wrap; gap:10px;
      margin-top: 14px;
    }}
    .chip {{
      padding: 9px 10px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.05);
      color: rgba(255,255,255,.82);
      font-size: 12px;
      display:flex; gap:8px; align-items:center;
    }}
    .chip b{{color:var(--txt)}}
    .cols {{
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    @media (max-width: 520px) {{
      .cols {{ grid-template-columns: 1fr; }}
    }}
    .tile {{
      padding: 14px;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.05);
    }}
    .tile h3 {{
      margin:0 0 6px;
      font-size: 14px;
      letter-spacing:.2px;
    }}
    .meta {{
      display:flex; gap:10px; flex-wrap:wrap;
      margin-top: 10px;
    }}
    .pill {{
      font-size: 12px;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.04);
      color: rgba(255,255,255,.78);
    }}
    .pill.ok {{ border-color: rgba(76,255,181,.25); }}
    .pill.warn {{ border-color: rgba(255,201,74,.25); }}
    .pill.bad {{ border-color: rgba(255,77,109,.25); }}
    .section-title {{
      margin: 18px 0 10px;
      font-size: 13px;
      letter-spacing:.4px;
      color: rgba(255,255,255,.80);
      text-transform: uppercase;
    }}
    .foot {{
      margin-top: 18px;
      display:flex;
      gap:10px;
      flex-wrap:wrap;
      justify-content:space-between;
      align-items:center;
      color: rgba(255,255,255,.55);
      font-size: 12px;
      padding: 0 6px;
    }}
    .foot a{{color: rgba(255,255,255,.70)}}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      color: rgba(255,255,255,.75);
    }}
  </style>
</head>
<body>
  <div class="grid"></div>

  <div class="wrap">
    <header>
      <div class="brand">
        <div class="logo" aria-hidden="true"></div>
        <div>
          <h1>Chronos</h1>
          <small>Señales MTF • Radar • Panel Profesional</small>
        </div>
      </div>

      <div class="top-actions">
        <a class="btn" href="{health_url}">Estado API</a>
        <a class="btn" href="{docs_url}">Docs</a>
        {"<a class='btn' href='"+tg_link+"' target='_blank' rel='noopener'>Telegram</a>" if tg_link else ""}
        {"<a class='btn primary' href='"+wa+"' target='_blank' rel='noopener'>WhatsApp • Activar Plan</a>" if wa else "<span class='btn primary' style='opacity:.7; cursor:not-allowed;'>WhatsApp • Configura WHATSAPP_CONTACT</span>"}
      </div>
    </header>

    <section class="hero">
      <div class="card">
        <div class="headline">
          <div class="kicker"><span class="dot"></span> Plataforma institucional-tecnológica, sin copiar a nadie</div>
          <h2>Decisiones rápidas, señales limpias.</h2>
          <p>
            Chronos prioriza claridad: ranking por <b>score</b>, radar de oportunidades y panel profesional.
            El plan <b>Free</b> es prueba de <b>7 días</b>. Al expirar, el usuario queda <b>bloqueado</b>
            hasta que el administrador active <b>Plus</b> o <b>Premium</b> por 30 días.
          </p>

          <div class="chips">
            <div class="chip">⚡ <b>En vivo</b> por Telegram</div>
            <div class="chip">🧠 <b>MTF</b> continuación + filtro</div>
            <div class="chip">🛡️ <b>Control</b> admin: activar / ban</div>
            <div class="chip">📈 <b>Ranking</b> Oro / Plata / Bronce</div>
          </div>
        </div>

        <div class="card pad">
          <div class="section-title">Planes (resumen visual)</div>
          <div class="cols">
            <div class="tile">
              <h3>Free • 7 días</h3>
              <p>Acceso limitado. Al día 8 pasa a <b>inactive</b> automáticamente.</p>
              <div class="meta">
                <span class="pill warn">Bronce</span>
                <span class="pill">Radar limitado</span>
                <span class="pill bad">Se bloquea</span>
              </div>
            </div>
            <div class="tile">
              <h3>Plus • 30 días</h3>
              <p>Señales Plata + Bronce. Radar completo.</p>
              <div class="meta">
                <span class="pill ok">Plata</span>
                <span class="pill">Radar completo</span>
                <span class="pill warn">Manual (admin)</span>
              </div>
            </div>
            <div class="tile">
              <h3>Premium • 30 días</h3>
              <p>Señales Oro + Plata + Bronce. Panel profesional.</p>
              <div class="meta">
                <span class="pill ok">Oro</span>
                <span class="pill">Centro de mercado</span>
                <span class="pill warn">Manual (admin)</span>
              </div>
            </div>
            <div class="tile">
              <h3>Admin • Control total</h3>
              <p>Activar planes, ban temporal/permanente y desbloqueo.</p>
              <div class="meta">
                <span class="pill">/admin</span>
                <span class="pill">lookup</span>
                <span class="pill">ban/unban</span>
              </div>
            </div>
          </div>

          <div class="section-title">Siguiente paso</div>
          <p style="margin-bottom:0">
            Cuando tú me digas, montamos la <b>portada real</b> con tus botones de navegación (Front),
            pero esta home ya te da una identidad única y coherente con Chronos.
          </p>
        </div>
      </div>

      <div class="card pad">
        <div class="section-title">Conexión rápida</div>
        <div class="tile" style="margin-bottom:12px">
          <h3>API viva</h3>
          <p>Tu backend responde y sirve documentación sin tocar nada más.</p>
          <div class="meta">
            <span class="pill ok">/health</span>
            <span class="pill ok">/docs</span>
          </div>
        </div>

        <div class="tile" style="margin-bottom:12px">
          <h3>Link de Telegram</h3>
          <p>El usuario vincula cuenta para recibir alertas en vivo.</p>
          <div class="meta">
            <span class="pill">/telegram/link-code</span>
            <span class="pill">/telegram/link</span>
          </div>
          <p class="mono" style="margin-top:10px">Bot: {("@"+tg_user) if tg_user else "Configura TELEGRAM_BOT_USERNAME"}</p>
        </div>

        <div class="tile">
          <h3>Activación manual</h3>
          <p>El pago es fuera del sistema. El usuario toca WhatsApp y tú activas plan desde admin.</p>
          <div class="meta">
            <span class="pill warn">Plus / Premium</span>
            <span class="pill">30 días</span>
            <span class="pill bad">No vuelve a Free</span>
          </div>
        </div>
      </div>
    </section>

    <div class="foot">
      <div>© {datetime.utcnow().year} Chronos • Señales con disciplina</div>
      <div>
        <a href="/docs">API Docs</a> · <a href="/openapi.json">OpenAPI</a>
      </div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

    if settings.admin_email and settings.admin_password:
        admin_email = settings.admin_email.strip()
        admin_password = settings.admin_password.strip()

        # Si alguien pone algo inválido, NO tumbar el backend.
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
            # Silencioso: el backend no debe caerse por bootstrap
            pass
