(function(){
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const state = {
    token: localStorage.getItem("chronos_token") || "",
    me: null,
  };

  function setTitle(title, subtitle){
    $("#viewTitle").textContent = title;
    $("#viewSubtitle").textContent = subtitle || "";
  }

  function setPill(text, ok=true){
    $("#pillText").textContent = text;
    const dot = $(".dot");
    dot.style.background = ok ? "#34d399" : "#fbbf24";
    dot.style.boxShadow = ok ? "0 0 0 4px rgba(52,211,153,.12)" : "0 0 0 4px rgba(251,191,36,.12)";
  }

  function openSidebar(open){
    const sb = $("#sidebar");
    const bd = $("#backdrop");
    if (open){
      sb.classList.add("open");
      bd.classList.remove("hidden");
    } else {
      sb.classList.remove("open");
      bd.classList.add("hidden");
    }
  }

  async function api(path, opts){
    const headers = Object.assign({"Content-Type":"application/json"}, (opts && opts.headers) || {});
    if (state.token) headers["Authorization"] = "Bearer " + state.token;
    const res = await fetch(path, Object.assign({}, opts || {}, {headers}));
    let data = null;
    try { data = await res.json(); } catch(e) {}
    if (!res.ok){
      const msg = (data && (data.detail || data.message)) || ("HTTP " + res.status);
      throw new Error(msg);
    }
    return data;
  }

  async function refreshMe(){
    try{
      const me = await api("/me");
      state.me = me;
      $("#meJson").textContent = JSON.stringify(me, null, 2);

      if (me && me.email){
        const label = me.account_state ? (me.account_state + " · " + me.plan) : (me.plan || "usuario");
        setPill(label, true);
      } else {
        setPill("Invitado", true);
      }
    }catch(err){
      $("#meJson").textContent = "{}";
      setPill("Invitado", true);
    }
  }

  function show(view){
    $$(".view").forEach(v => v.classList.add("hidden"));
    const el = document.querySelector(`.view[data-view="${view}"]`);
    if (el) el.classList.remove("hidden");

    $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.view === view));

    const titles = {
      dashboard: ["Dashboard", "Centro de control"],
      signals: ["Señales", "Ranking y ejecución"],
      radar: ["Radar", "Oportunidades del mercado"],
      account: ["Cuenta", "Perfil y plan"],
      support: ["Soporte", "Ayuda y contacto"],
    };
    const t = titles[view] || ["Chronos",""];
    setTitle(t[0], t[1]);
    if (window.innerWidth < 900) openSidebar(false);
  }

  function route(){
    const hash = (location.hash || "#/dashboard").replace("#/","");
    const view = hash.split("?")[0] || "dashboard";
    show(view);
  }

  // UI handlers
  $("#btnMenu").addEventListener("click", () => openSidebar(true));
  $("#backdrop").addEventListener("click", () => openSidebar(false));
  $("#btnExit").addEventListener("click", () => { openSidebar(false); location.hash = "#/dashboard"; });

  $("#btnOpenDocs").addEventListener("click", () => { window.open("/docs", "_blank"); });

  $("#btnRefreshMe").addEventListener("click", () => refreshMe());

  $("#btnWhats").addEventListener("click", async (e) => {
    e.preventDefault();
    // El backend expone settings en /health? no. Por ahora solo placeholder.
    alert("WhatsApp se configura en el backend (settings.whatsapp_contact).");
  });

  window.addEventListener("hashchange", route);

  // boot
  route();
  refreshMe();
})();
