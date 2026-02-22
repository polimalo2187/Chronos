/* Chronos UI v0.1 - session + routing (JWT) */
const $ = (sel) => document.querySelector(sel);

const state = {
  route: "dashboard",
  token: localStorage.getItem("chronos_token") || "",
  me: null,
};

function setStatus(text, color) {
  $("#statusText").textContent = text;
  const dot = $("#statusDot");
  dot.style.background = color || "rgba(255,255,255,.18)";
}

function setTitle(title, sub) {
  $("#pageTitle").textContent = title;
  $("#pageSub").textContent = sub || "";
}

function showView(route) {
  document.querySelectorAll(".view").forEach(v => {
    v.classList.toggle("hidden", v.dataset.view !== route);
  });

  document.querySelectorAll(".nav-item").forEach(b => {
    b.classList.toggle("active", b.dataset.route === route);
  });

  const map = {
    dashboard: ["Dashboard", "Centro de control"],
    signals: ["Señales", "Ranking y ejecución"],
    radar: ["Radar", "Oportunidades del mercado"],
    account: ["Cuenta", "Perfil y plan"],
    support: ["Soporte", "Ayuda y contacto"],
  };
  const [t, s] = map[route] || ["Chronos", ""];
  setTitle(t, s);
}

function openSidebar(open) {
  const sb = $("#sidebar");
  if (!sb) return;
  sb.classList.toggle("open", !!open);
}

async function api(path, { method="GET", body=null, auth=true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : null });
  const txt = await res.text();
  let data = null;
  try { data = txt ? JSON.parse(txt) : null; } catch { data = { raw: txt }; }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2); } catch { return String(obj); }
}

function applyGates() {
  // gates only affect UI placeholders for now
  const plan = (state.me && state.me.plan) ? String(state.me.plan).toLowerCase() : "guest";

  // Radar: full for plus/premium, limited for free/guest
  const radarGate = $("#radarGate");
  if (radarGate) radarGate.classList.toggle("hidden", plan === "plus" || plan === "premium");

  // Signals: guest/free limited banner (still can view placeholders)
  const signalsGate = $("#signalsGate");
  if (signalsGate) signalsGate.classList.toggle("hidden", !(plan === "guest" || plan === "free"));
}

function setMe(me) {
  state.me = me || null;

  if (!state.me) {
    setStatus("Invitado", "rgba(255,255,255,.18)");
    $("#meJson").textContent = "{}";
    applyGates();
    return;
  }

  const p = (state.me.plan || "free").toString();
  const up = p.charAt(0).toUpperCase() + p.slice(1);
  const ok = (state.me.status || "active").toString();
  const label = ok === "banned" ? `${up} • Banned` :
                ok === "inactive" ? `${up} • Inactive` :
                up;

  const color = ok === "banned" ? "var(--bad)" : (ok === "inactive" ? "var(--warn)" : "var(--good)");
  setStatus(label, color);
  $("#meJson").textContent = pretty(state.me);
  applyGates();
}

async function loadMe() {
  if (!state.token) {
    setMe(null);
    return;
  }
  try {
    // preferred route (we add this on backend for convenience)
    const me = await api("/auth/me", { auth: true });
    setMe(me);
  } catch (e) {
    // token invalid -> logout
    logout(true);
  }
}

function setAuthMsg(msg) {
  const el = $("#authMsg");
  if (!el) return;
  el.textContent = msg || "";
}

async function doRegister() {
  setAuthMsg("");
  const email = $("#email").value.trim();
  const password = $("#password").value;
  if (!email || !password) return setAuthMsg("Completa email y password.");

  try {
    await api("/auth/register", { method:"POST", auth:false, body:{ email, password }});
    setAuthMsg("Registrado. Ahora haz login.");
  } catch (e) {
    setAuthMsg(e.message);
  }
}

async function doLogin() {
  setAuthMsg("");
  const email = $("#email").value.trim();
  const password = $("#password").value;
  if (!email || !password) return setAuthMsg("Completa email y password.");

  try {
    const data = await api("/auth/login", { method:"POST", auth:false, body:{ email, password }});
    const token = data.access_token || data.token || "";
    if (!token) throw new Error("No llegó access_token.");
    state.token = token;
    localStorage.setItem("chronos_token", token);
    setAuthMsg("OK. Sesión iniciada.");
    await loadMe();
    showView("dashboard");
  } catch (e) {
    setAuthMsg(e.message);
  }
}

function logout(silent=false) {
  state.token = "";
  localStorage.removeItem("chronos_token");
  setMe(null);
  if (!silent) setAuthMsg("Sesión cerrada.");
}

async function copyToken() {
  if (!state.token) return setAuthMsg("No hay token.");
  try {
    await navigator.clipboard.writeText(state.token);
    setAuthMsg("Token copiado.");
  } catch {
    setAuthMsg("No pude copiar. (Android a veces bloquea clipboard)");
  }
}

async function openWhatsApp() {
  try {
    const data = await api("/api/whatsapp", { auth:false });
    if (data && data.url) {
      window.open(data.url, "_blank");
      $("#supportMsg").textContent = "Abriendo WhatsApp…";
    } else {
      $("#supportMsg").textContent = "WhatsApp no configurado.";
    }
  } catch {
    $("#supportMsg").textContent = "WhatsApp no configurado.";
  }
}

function bindUI() {
  // nav
  $("#nav").addEventListener("click", (e) => {
    const btn = e.target.closest(".nav-item");
    if (!btn) return;
    const r = btn.dataset.route;
    if (r === "logout") {
      logout();
      showView("dashboard");
      openSidebar(false);
      return;
    }
    showView(r);
    openSidebar(false);
  });

  // burger
  $("#burger").addEventListener("click", () => openSidebar(true));
  document.addEventListener("click", (e) => {
    const sb = $("#sidebar");
    if (!sb) return;
    if (!sb.classList.contains("open")) return;
    const inside = sb.contains(e.target) || $("#burger").contains(e.target);
    if (!inside) openSidebar(false);
  });

  // auth
  $("#btnRegister").addEventListener("click", doRegister);
  $("#btnLogin").addEventListener("click", doLogin);
  $("#btnCopyToken").addEventListener("click", copyToken);
  $("#btnLogout").addEventListener("click", () => { logout(); showView("dashboard"); });

  // account
  $("#btnRefreshMe").addEventListener("click", loadMe);

  // support
  $("#btnWhatsApp").addEventListener("click", openWhatsApp);
}

async function boot() {
  bindUI();
  showView("dashboard");
  await loadMe();
}

boot();
