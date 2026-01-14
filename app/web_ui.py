# app/web_ui.py

from typing import Dict, Optional
from datetime import datetime

# ======================================================
# CONFIGURACIÓN DE COLORES POR NIVEL DE RIESGO
# ======================================================

RISK_COLORS = {
    "conservador": "#4CAF50",  # verde
    "moderado": "#FFEB3B",     # amarillo
    "agresivo": "#F44336",     # rojo
}

# ======================================================
# FUNCIONES DE INTERFAZ
# ======================================================

def render_message_centered(message: str) -> str:
    """
    Renderiza un mensaje simple centrado en pantalla.
    """
    html = f"""
    <div style="display:flex; justify-content:center; align-items:center; height:100vh;">
        <div style="text-align:center; font-family:sans-serif; padding:20px;">
            {message}
        </div>
    </div>
    """
    return html


def render_alert_no_signal() -> str:
    """
    Muestra mensaje cuando no hay señales disponibles.
    """
    message = "<h2>📭 Sin señal disponible</h2><p>Proceso de escaneo de mercado...</p>"
    return render_message_centered(message)


def render_back_button() -> str:
    """
    Botón para regresar al menú principal.
    """
    html = """
    <div style="display:flex; justify-content:center; margin-top:20px;">
        <button onclick="goBack()" style="padding:10px 20px; font-size:16px;">⬅️ Volver al menú</button>
    </div>
    <script>
    function goBack() {
        // Función que se conecta a la lógica de la web para volver al menú
        if(window.handleBackMenu) window.handleBackMenu();
    }
    </script>
    """
    return html


def render_signal_card(signal: Dict) -> str:
    """
    Renderiza la señal completa en una tarjeta con colores por nivel.
    `signal` debe contener:
        - symbol, direction, entry, stop_loss, take_profits
        - timeframes, visibility, leverage
        - margin_mode, created_at, id
    """

    # Construir HTML por niveles
    sections_html = ""
    for level in ["conservador", "moderado", "agresivo"]:
        lvl_data = signal.get("leverage", {}).get(level, "")
        sections_html += f"""
        <div style="
            background-color:{RISK_COLORS[level]};
            color:{'#000' if level != 'agresivo' else '#fff'};
            padding:15px; margin:10px 0; border-radius:10px;">
            <h3>{level.upper()}</h3>
            <p>SL: {signal.get('stop_loss')}</p>
            <p>TP1: {signal.get('take_profits')[0] if len(signal.get('take_profits'))>0 else '-'}</p>
            <p>TP2: {signal.get('take_profits')[1] if len(signal.get('take_profits'))>1 else '-'}</p>
            <p>Apalancamiento: {lvl_data}</p>
        </div>
        """

    # Cabecera de la señal
    html = f"""
    <div style="display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <div style="width:90%; max-width:600px; background:#f5f5f5; padding:20px; border-radius:15px;">
            <h2>📊 NUEVA SEÑAL – FUTUROS USDT</h2>
            <p>🏷️ PLAN: {signal.get('visibility', 'FREE')}</p>
            <p>Par: {signal.get('symbol')}</p>
            <p>Dirección: {signal.get('direction')}</p>
            <p>Zona de entrada: {signal.get('entry')}</p>
            <p>⏱️ Tiempo estimado a zona de entrada: ≈ 1 – 5 minutos</p>
            <p>⏳ Vigencia: {signal.get('created_at', datetime.utcnow()).strftime('%H:%M')} minutos</p>
            <p>Margen: {signal.get('margin_mode', 'ISOLATED')}</p>
            <p>Timeframes: {" / ".join(signal.get('timeframes', []))}</p>
            <hr>
            {sections_html}
            <p>🔐 ID: {signal.get('id', '')}</p>
            {render_back_button()}
        </div>
    </div>
    """
    return html
