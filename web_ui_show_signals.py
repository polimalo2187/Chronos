# web_ui_show_signals.py

from datetime import datetime
from typing import List, Dict, Optional

# ======================================================
# COLORES DE LAS TARJETAS
# ======================================================
CARD_COLORS = {
    "conservador": "#4CAF50",  # verde
    "moderado": "#FFC107",     # amarillo
    "agresivo": "#F44336",     # rojo
}

# ======================================================
# MENSAJE SIN SEÑALES
# ======================================================

def show_no_signals_message() -> Dict[str, str]:
    """
    Retorna el mensaje cuando no hay señales disponibles.
    """
    return {
        "title": "📭 No hay señales disponibles",
        "subtitle": "Proceso de escaneo de mercado en curso…",
        "centered": True
    }

# ======================================================
# RENDERIZADO DE SEÑAL
# ======================================================

def render_signal_card(signal: Dict[str, any]) -> Dict[str, any]:
    """
    Recibe un diccionario con la información de la señal y retorna la tarjeta
    lista para mostrar en la web.
    """
    # Datos básicos
    card = {
        "title": "📊 NUEVA SEÑAL – FUTUROS USDT",
        "plan": signal.get("visibility", "FREE").upper(),
        "symbol": signal.get("symbol"),
        "direction": signal.get("direction"),
        "entry_zone": signal.get("entry"),
        "eta_entry": signal.get("eta_entry", "≈ 1 – 5 minutos"),
        "expiry": signal.get("expiry", "07:24 minutos"),
        "margin_mode": signal.get("margin_mode", "ISOLATED"),
        "timeframes": " / ".join(signal.get("timeframes", [])),
        "id": signal.get("id", "N/A"),
        "centered": True,
        "sections": []
    }

    # Secciones de riesgo: conservador, moderado, agresivo
    for risk_level in ["conservador", "moderado", "agresivo"]:
        data = signal.get("leverage", {}).get(risk_level, {})
        section = {
            "name": risk_level.capitalize(),
            "color": CARD_COLORS[risk_level],
            "sl": data.get("sl", "N/A"),
            "tp1": data.get("tp1", "N/A"),
            "tp2": data.get("tp2", "N/A"),
            "leverage": data.get("leverage", signal.get("leverage", {}).get(risk_level, "N/A")),
        }
        card["sections"].append(section)

    return card

# ======================================================
# OBTENER SEÑALES DEL USUARIO
# ======================================================

def get_signals_for_user(user: Dict[str, any], signals_db: List[Dict[str, any]]) -> Optional[List[Dict[str, any]]]:
    """
    Filtra señales por plan y visibilidad del usuario.
    """
    user_plan = user.get("plan", "FREE").upper()
    eligible_signals = []

    for signal in signals_db:
        if signal.get("visibility", "FREE").upper() == user_plan:
            eligible_signals.append(render_signal_card(signal))

    if not eligible_signals:
        return None
    return eligible_signals

# ======================================================
# FUNCION PRINCIPAL DEL BOTÓN "VER SEÑALES"
# ======================================================

def handle_view_signals(user: Dict[str, any], signals_db: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Maneja la acción del botón 'Ver señales'.
    Devuelve lista de tarjetas o mensaje sin señales.
    """
    cards = get_signals_for_user(user, signals_db)
    if not cards:
        return [show_no_signals_message()]

    # Agregar siempre un botón de volver al final de cada tarjeta
    for card in cards:
        card["back_button"] = {
            "label": "⬅️ Volver",
            "action": "back_to_menu"
        }

    return cards
