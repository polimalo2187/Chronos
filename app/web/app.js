(function(){
  const API = window.location.origin;

  const $ = (id)=>document.getElementById(id);
  const toast = (el, msg)=>{ el.textContent = msg || ""; };

  function setHint(msg){ $("hint").textContent = msg || ""; }

  function setStatus(ok, text){
    $("statusText").textContent = text;
    const dot = $("dot");
    dot.style.background = ok ? "rgba(77,214,255,.95)" : "rgba(255,255,255,.25)";
    dot.style.boxShadow = ok ? "0 0 0 6px rgba(77,214,255,.08)" : "none";
  }

  function getToken(){ return localStorage.getItem("chronos_token") || ""; }
  function setToken(t){ localStorage.setItem("chronos_token", t || ""); }
  function clearToken(){ localStorage.removeItem("chronos_token"); }

  async function apiFetch(path, opts){
    const headers = Object.assign({"Content-Type":"application/json"}, (opts && opts.headers) || {});
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    const res = await fetch(API + path, Object.assign({}, opts || {}, { headers }));
    const text = await res.text();
    let data = null;
    try{ data = text ? JSON.parse(text) : null; }catch(e){ data = { raw: text }; }
    if (!res.ok){
      const msg = (data && (data.detail || data.message)) || ("HTTP " + res.status);
      throw new Error(msg);
    }
    return data;
  }

  async function ping(){
    try{
      await apiFetch("/health", { method: "GET", headers: {} });
      setStatus(true, "API viva · Portada HTML activa");
    }catch(e){
      setStatus(false, "Sin conexión a API");
    }
  }

  function selectTab(name){
    document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
    document.querySelectorAll(".tabpane").forEach(p=>p.classList.remove("show"));
    document.querySelector(`.tab[data-tab="${name}"]`)?.classList.add("active");
    $("tab-"+name)?.classList.add("show");
  }

  async function refreshMe(){
    const out = $("meJson");
    const toastEl = $("toastMe");
    toast(toastEl, "");
    out.textContent = "{}";
    try{
      const me = await apiFetch("/me", { method: "GET" });
      out.textContent = JSON.stringify(me, null, 2);

      // Habilitar Admin tab si es_admin
      const isAdmin = !!me.is_admin;
      $("tabAdmin").disabled = !isAdmin;
      if (isAdmin){
        setHint("Modo admin detectado. Puedes abrir la pestaña Admin.");
      }
    }catch(e){
      toast(toastEl, "Error: " + e.message);
    }
  }

  async function doRegister(){
    const t = $("toastAuth");
    toast(t, "");
    try{
      const email = $("regEmail").value.trim();
      const password = $("regPass").value;
      const data = await apiFetch("/auth/register", { method:"POST", body: JSON.stringify({ email, password }) });
      setToken(data.access_token);
      toast(t, "Registrado OK. Token guardado.");
      await refreshMe();
      selectTab("me");
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  async function doLogin(){
    const t = $("toastAuth");
    toast(t, "");
    try{
      const email = $("logEmail").value.trim();
      const password = $("logPass").value;
      const data = await apiFetch("/auth/login", { method:"POST", body: JSON.stringify({ email, password }) });
      setToken(data.access_token);
      toast(t, "Login OK. Token guardado.");
      await refreshMe();
      selectTab("me");
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  function doLogout(){
    clearToken();
    $("tabAdmin").disabled = true;
    $("meJson").textContent = "{}";
    toast($("toastAuth"), "Sesión cerrada.");
    setHint("Token borrado. Vuelve a iniciar sesión.");
    selectTab("auth");
  }

  async function doLookup(){
    const out = $("lkJson");
    const t = $("toastAdmin");
    toast(t, "");
    out.textContent = "{}";
    try{
      const email = $("lkEmail").value.trim() || null;
      const telegram_id = $("lkTg").value ? parseInt($("lkTg").value, 10) : null;
      const data = await apiFetch("/admin/users/lookup", { method:"POST", body: JSON.stringify({ email, telegram_id }) });
      out.textContent = JSON.stringify(data, null, 2);
      if (data.user_id) $("bnUserId").value = data.user_id;
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  async function doActivate(){
    const out = $("adminJson");
    const t = $("toastAdmin");
    toast(t, "");
    out.textContent = "{}";
    try{
      const email = $("acEmail").value.trim() || null;
      const telegram_id = $("acTg").value ? parseInt($("acTg").value, 10) : null;
      const plan = $("acPlan").value;
      const data = await apiFetch("/admin/plan/activate", { method:"POST", body: JSON.stringify({ email, telegram_id, plan }) });
      out.textContent = JSON.stringify(data, null, 2);
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  async function doBan(days, permanent){
    const out = $("adminJson");
    const t = $("toastAdmin");
    toast(t, "");
    out.textContent = "{}";
    try{
      const user_id = $("bnUserId").value.trim();
      if (!user_id) throw new Error("Falta user_id");
      const payload = permanent ? { permanent: true } : { permanent: false, days: days || 7 };
      const data = await apiFetch(`/admin/users/${user_id}/ban`, { method:"POST", body: JSON.stringify(payload) });
      out.textContent = JSON.stringify(data, null, 2);
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  async function doUnban(){
    const out = $("adminJson");
    const t = $("toastAdmin");
    toast(t, "");
    out.textContent = "{}";
    try{
      const user_id = $("bnUserId").value.trim();
      if (!user_id) throw new Error("Falta user_id");
      const data = await apiFetch(`/admin/users/${user_id}/unban`, { method:"POST" });
      out.textContent = JSON.stringify(data, null, 2);
    }catch(e){
      toast(t, "Error: " + e.message);
    }
  }

  function wire(){
    // hero
    $("btnDocs").addEventListener("click", ()=>window.location.href = "/docs");
    $("btnHealth").addEventListener("click", async ()=>{
      try{ await apiFetch("/health", { method:"GET", headers:{} }); setHint("Health OK."); }
      catch(e){ setHint("Health FAIL: " + e.message); }
    });
    $("btnGoAuth").addEventListener("click", ()=>selectTab("auth"));
    $("btnOpenSwagger").addEventListener("click", ()=>window.location.href = "/docs");

    // tabs
    document.querySelectorAll(".tab").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        if (btn.disabled) return;
        selectTab(btn.dataset.tab);
      });
    });

    // auth
    $("btnRegister").addEventListener("click", doRegister);
    $("btnLogin").addEventListener("click", doLogin);
    $("btnLogout").addEventListener("click", doLogout);
    $("btnCopyToken").addEventListener("click", async ()=>{
      const t = getToken();
      try{
        await navigator.clipboard.writeText(t);
        toast($("toastAuth"), "Token copiado.");
      }catch(e){
        toast($("toastAuth"), "No pude copiar. Token: " + (t ? t.slice(0,20)+"…" : "(vacío)"));
      }
    });

    // me
    $("btnRefreshMe").addEventListener("click", refreshMe);

    // admin
    $("btnLookup").addEventListener("click", doLookup);
    $("btnActivate").addEventListener("click", doActivate);
    $("btnBan7").addEventListener("click", ()=>doBan(7,false));
    $("btnBanPerm").addEventListener("click", ()=>doBan(null,true));
    $("btnUnban").addEventListener("click", doUnban);
  }

  async function boot(){
    wire();
    await ping();
    if (getToken()){
      await refreshMe();
      selectTab("me");
    }else{
      selectTab("auth");
    }
  }

  boot();
})();
