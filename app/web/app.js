/* Chronos Web App UI (v0.1)
   - Session (JWT) stored in localStorage
   - Loads /me (fallback /auth/me) to render plan/status
   - Simple client-side gates (UI only)
*/

const TOKEN_KEY = "chronos_token";

function qs(sel) { return document.querySelector(sel); }
function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra = {}) {
  const h = { ...extra };
  const t = getToken();
  if (t) h["Authorization"] = `Bearer ${t}`;
  return h;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    ...opts,
    headers: authHeaders({
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    }),
  });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json().catch(() => null) : await res.text().catch(() => null);
  if (!res.ok) {
    const msg = (data && data.detail) ? data.detail : (typeof data === "string" ? data : `HTTP ${res.status}`);
    throw new Error(msg);
  }
  return data;
}

function fmtDate(iso) {
  try {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return String(iso || "—");
  }
}

// ---------- UI state ----------

let currentUser = null;

function setStatusPill({ label, ok = true }) {
  const statusText = qs("#statusText");
  const dot = qs("#statusDot");
  if (statusText) statusText.textContent = label;
  if (dot) dot.style.opacity = ok ? "1" : "0.35";
}

function renderMe(me) {
  currentUser = me || null;

  // Status pill
  if (!me) {
    setStatusPill({ label: "Invitado", ok: false });
  } else {
    const plan = (me.plan || "free").toString().toUpperCase();
    const state = (me.account_state || me.status || "active").toString();
    const ok = state === "active";
    setStatusPill({ label: `${plan}`, ok });
  }

  // JSON viewer
  const pre = qs("#meJson");
  if (pre) pre.textContent = me ? JSON.stringify({
    email: me.email,
    plan: me.plan,
    plan_expires_at: fmtDate(me.plan_expires_at),
    account_state: me.account_state,
    is_admin: !!me.is_admin,
    telegram_id: me.telegram_id,
    telegram_username: me.telegram_username,
    telegram_linked: !!me.telegram_linked,
  }, null, 2) : "{}";

  // Gates (UI only)
  const planKey = (me?.plan || "guest").toLowerCase();
  const isLogged = !!me;
  const isPlusOrPremium = planKey === "plus" || planKey === "premium";

  const signalsGate = qs("#signalsGate");
  const radarGate = qs("#radarGate");

  // Signals: allow guest to see placeholder, but show warning if not logged
  if (signalsGate) {
    const show = !isLogged;
    signalsGate.classList.toggle("hidden", !show);
  }

  // Radar: full radar requires plus/premium (for now)
  if (radarGate) {
    const show = !isPlusOrPremium;
    radarGate.classList.toggle("hidden", !show);
  }

  // Admin nav item visibility (if you add it later)
  qsa('[data-route="admin"]').forEach((el) => {
    el.style.display = (me && me.is_admin) ? "" : "none";
  });
}

async function loadMe() {
  const token = getToken();
  if (!token) {
    renderMe(null);
    return;
  }

  try {
    // Prefer /me (exists in this repo). Fallback to /auth/me.
    let me;
    try {
      me = await api("/me", { method: "GET" });
    } catch {
      me = await api("/auth/me", { method: "GET" });
    }
    renderMe(me);
  } catch (e) {
    // Token invalid/expired
    clearToken();
    renderMe(null);
    const msg = qs("#authMsg");
    if (msg) msg.textContent = `Sesión inválida: ${e.message}`;
  }
}

// ---------- Routing (app-like navigation) ----------

const ROUTES = {
  dashboard: { title: "Dashboard", sub: "Centro de control" },
  signals: { title: "Señales", sub: "Ranking y ejecución" },
  radar: { title: "Radar", sub: "Oportunidades del mercado" },
  account: { title: "Cuenta", sub: "Perfil y plan" },
  support: { title: "Soporte", sub: "Ayuda y contacto" },
};

function showView(name) {
  // toggle views
  qsa(".view").forEach((v) => {
    const is = v.getAttribute("data-view") === name;
    v.classList.toggle("hidden", !is);
  });

  // nav active state
  qsa(".nav-item").forEach((b) => {
    const r = b.getAttribute("data-route");
    b.classList.toggle("active", r === name);
  });

  // header titles
  const meta = ROUTES[name] || { title: "Chronos", sub: "" };
  const h1 = qs("#pageTitle");
  const h2 = qs("#pageSub");
  if (h1) h1.textContent = meta.title;
  if (h2) h2.textContent = meta.sub;

  // close sidebar in mobile
  document.body.classList.remove("sidebar-open");
}

function bindRouting() {
  qsa(".nav-item").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const r = btn.getAttribute("data-route");
      if (!r) return;

      if (r === "logout") {
        clearToken();
        renderMe(null);
        showView("dashboard");
        return;
      }

      showView(r);
    });
  });
}

function bindBurger() {
  const burger = qs("#burger");
  if (!burger) return;
  burger.addEventListener("click", () => {
    document.body.classList.toggle("sidebar-open");
  });
}

// ---------- Auth actions ----------

async function doRegister(email, password) {
  const out = await api("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return out;
}

async function doLogin(email, password) {
  const out = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  const token = out?.access_token;
  if (!token) throw new Error("No llegó access_token");
  setToken(token);
  return token;
}

function bindAuthUI() {
  const emailEl = qs("#email");
  const passEl = qs("#password");
  const msg = qs("#authMsg");

  const btnReg = qs("#btnRegister");
  const btnLogin = qs("#btnLogin");
  const btnCopy = qs("#btnCopyToken");
  const btnRefresh = qs("#btnRefreshMe");

  const safeSetMsg = (t) => { if (msg) msg.textContent = t || ""; };

  if (btnReg) {
    btnReg.addEventListener("click", async () => {
      try {
        safeSetMsg("Registrando...");
        const email = (emailEl?.value || "").trim();
        const password = (passEl?.value || "").trim();
        if (!email || !password) throw new Error("Email y password requeridos");
        await doRegister(email, password);
        safeSetMsg("✅ Registro OK. Ahora haz login.");
      } catch (e) {
        safeSetMsg(`❌ ${e.message}`);
      }
    });
  }

  if (btnLogin) {
    btnLogin.addEventListener("click", async () => {
      try {
        safeSetMsg("Iniciando sesión...");
        const email = (emailEl?.value || "").trim();
        const password = (passEl?.value || "").trim();
        if (!email || !password) throw new Error("Email y password requeridos");
        await doLogin(email, password);
        await loadMe();
        safeSetMsg("✅ Sesión iniciada.");
        showView("dashboard");
      } catch (e) {
        safeSetMsg(`❌ ${e.message}`);
      }
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener("click", async () => {
      try {
        const t = getToken();
        if (!t) throw new Error("No hay token aún");
        await navigator.clipboard.writeText(t);
        safeSetMsg("✅ Token copiado.");
      } catch (e) {
        safeSetMsg(`❌ ${e.message}`);
      }
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener("click", async () => {
      try {
        safeSetMsg("Actualizando...");
        await loadMe();
        safeSetMsg("✅ Actualizado.");
      } catch (e) {
        safeSetMsg(`❌ ${e.message}`);
      }
    });
  }
}

function bindSupport() {
  const btn = qs("#btnWhatsApp");
  const msg = qs("#supportMsg");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      const settings = await api("/health/settings", { method: "GET", headers: { "Content-Type": "application/json" } });
      const url = settings?.whatsapp_contact;
      if (!url) {
        if (msg) msg.textContent = "WhatsApp no configurado en settings.";
        return;
      }
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      if (msg) msg.textContent = "WhatsApp no configurado.";
    }
  });
}

// ---------- Boot ----------

document.addEventListener("DOMContentLoaded", async () => {
  bindBurger();
  bindRouting();
  bindAuthUI();
  bindSupport();

  // default view
  showView("dashboard");
  await loadMe();
});
