// Chronos App Router (no framework)
(function () {
  const viewRoot = document.getElementById("viewRoot");
  const pageTitle = document.getElementById("pageTitle");
  const pageSub = document.getElementById("pageSub");
  const btnSidebar = document.getElementById("btnSidebar");
  const sidebar = document.querySelector(".sidebar");
  const navItems = Array.from(document.querySelectorAll(".nav-item[data-route]"));

  const routes = {
    dashboard: {
      title: "Dashboard",
      sub: "Centro de control",
      render: renderDashboard,
    },
    signals: {
      title: "Señales",
      sub: "Listado de señales activas",
      render: renderSignals,
    },
    radar: {
      title: "Radar",
      sub: "Oportunidades del mercado",
      render: renderRadar,
    },
    account: {
      title: "Cuenta",
      sub: "Perfil y plan",
      render: renderAccount,
    },
    support: {
      title: "Soporte",
      sub: "Ayuda y contacto",
      render: renderSupport,
    },
    logout: {
      title: "Salir",
      sub: "Cerrar sesión",
      render: renderLogout,
    },
  };

  function setActive(route) {
    navItems.forEach((btn) => btn.classList.toggle("is-active", btn.dataset.route === route));
  }

  function navigate(route) {
    const r = routes[route] ? route : "dashboard";
    const cfg = routes[r];

    pageTitle.textContent = cfg.title;
    pageSub.textContent = cfg.sub;
    setActive(r);

    // render
    viewRoot.innerHTML = "";
    cfg.render(viewRoot);

    // close sidebar on mobile
    if (sidebar && sidebar.classList.contains("is-open")) sidebar.classList.remove("is-open");

    // update hash
    if (location.hash !== "#" + r) location.hash = "#" + r;
  }

  // Views (placeholders)
  function renderDashboard(root) {
    root.innerHTML = `
      <div class="grid">
        <div class="card">
          <h3>Estado del mercado</h3>
          <p>Placeholder visual. Aquí irá tu “Estado del Mercado” (Premium).</p>
          <div class="kpi">
            <div class="value">—</div>
            <div class="tag">Sin datos aún</div>
          </div>
        </div>
        <div class="card">
          <h3>Señales recientes</h3>
          <p>Placeholder. Aquí mostraremos las 3 mejores señales por score (según plan).</p>
          <table class="table">
            <thead><tr><th>Par</th><th>Dir</th><th>Score</th><th>Estado</th></tr></thead>
            <tbody>
              <tr><td>—</td><td>—</td><td>—</td><td><span class="badge">Sin datos</span></td></tr>
            </tbody>
          </table>
        </div>
        <div class="card">
          <h3>Radar de oportunidades</h3>
          <p>Placeholder. Ranking de oportunidades (Oro/Plata/Bronce).</p>
        </div>
        <div class="card">
          <h3>Alertas</h3>
          <p>Placeholder. Notificaciones en vivo (Telegram / push más adelante).</p>
        </div>
      </div>
    `;
  }

  function renderSignals(root) {
    root.innerHTML = `
      <div class="card" style="grid-column: span 12;">
        <h3>Señales</h3>
        <p>Vista placeholder. Aquí va el feed de señales filtrado por plan.</p>
        <table class="table">
          <thead><tr><th>Hora</th><th>Par</th><th>Dir</th><th>TF</th><th>Score</th><th>Tier</th></tr></thead>
          <tbody>
            <tr><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td><span class="badge warn">Bronce</span></td></tr>
          </tbody>
        </table>
      </div>
    `;
  }

  function renderRadar(root) {
    root.innerHTML = `
      <div class="grid">
        <div class="card" style="grid-column: span 12;">
          <h3>Radar</h3>
          <p>Placeholder. Aquí se listan oportunidades por score y volatilidad.</p>
          <div class="kpi">
            <div class="value">—</div>
            <div class="tag">Scanner aún no conectado</div>
          </div>
        </div>
      </div>
    `;
  }

  function renderAccount(root) {
    root.innerHTML = `
      <div class="grid">
        <div class="card">
          <h3>Perfil</h3>
          <p>Placeholder. Mostrar email, plan, expiración y estado.</p>
        </div>
        <div class="card">
          <h3>Plan</h3>
          <p>Placeholder. Botón para renovar por WhatsApp (desde settings.whatsapp_contact).</p>
          <span class="badge good">Plus/Premium: 30 días</span>
        </div>
      </div>
    `;
  }

  function renderSupport(root) {
    root.innerHTML = `
      <div class="grid">
        <div class="card" style="grid-column: span 12;">
          <h3>Soporte</h3>
          <p>Placeholder. FAQ + enlace WhatsApp.</p>
        </div>
      </div>
    `;
  }

  function renderLogout(root) {
    root.innerHTML = `
      <div class="grid">
        <div class="card" style="grid-column: span 12;">
          <h3>Salir</h3>
          <p>Placeholder. Aquí luego borramos token del storage y redirigimos a /login.</p>
          <span class="badge bad">Sesión</span>
        </div>
      </div>
    `;
  }

  // Events
  navItems.forEach((btn) => btn.addEventListener("click", () => navigate(btn.dataset.route)));

  if (btnSidebar) {
    btnSidebar.addEventListener("click", () => {
      if (!sidebar) return;
      sidebar.classList.toggle("is-open");
    });
  }

  // init route from hash
  const initial = (location.hash || "#dashboard").replace("#", "");
  navigate(initial);
})();
