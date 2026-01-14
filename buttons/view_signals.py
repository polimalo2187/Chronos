# buttons/view_signals.py

from datetime import datetime
from app.database import signals_collection
from app.models import is_plan_active, is_trial_active, update_timestamp
from app.plans import PLAN_FREE, PLAN_PLUS, PLAN_PREMIUM, generate_user_signal, format_user_signal
from app.web_ui import show_card, show_message, add_back_button  # Funciones de UI para web

def get_latest_signals_for_user(user):
    """
    Obtiene las últimas señales disponibles para el usuario según su plan.
    """
    plan = PLAN_PREMIUM if user.get("is_admin") else user.get("plan", PLAN_FREE)
    
    if not user.get("is_admin") and not (is_plan_active(user) or is_trial_active(user)):
        return None, "⛔ Acceso expirado."
    
    signals = signals_collection().find({"visibility": plan}).sort("created_at", -1).limit(1)
    if not signals:
        return None, "📭 No hay señales disponibles.\n⏳ Proceso de escaneo de mercado…"
    
    return signals, None


def render_signal_card(signal, user):
    """
    Renderiza la señal en tarjetas coloreadas por nivel.
    """
    # Bloque general
    header = (
        f"📊 NUEVA SEÑAL – FUTUROS USDT\n\n"
        f"🏷️ PLAN: {signal['visibility'].upper()}\n"
        f"Par: {signal['symbol']}\n"
        f"Dirección: {signal['direction']}\n"
        f"Zona de entrada: {signal['entry']}\n"
        f"⏱️ Tiempo estimado a zona de entrada: ≈ 1 – 5 minutos\n"
        f"⏳ Vigencia: {signal.get('expires_at', 'N/A')}\n"
        f"Margen: {signal.get('margin_mode', 'ISOLATED')}\n"
        f"Timeframes: {' / '.join(signal['timeframes'])}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    # Bloques de niveles con color
    level_blocks = [
        ("CONSERVADOR", signal['leverage']['conservador'], "#4CAF50"),  # verde
        ("MODERADO", signal['leverage']['moderado'], "#FFEB3B"),        # amarillo
        ("AGRESIVO", signal['leverage']['agresivo'], "#F44336"),        # rojo
    ]
    
    cards = []
    for level_name, leverage_range, color in level_blocks:
        block = (
            f"{level_name}\n"
            f"SL: {signal['stop_loss']}\n"
            f"TP1: {signal['take_profits'][0]}\n"
            f"TP2: {signal['take_profits'][1]}\n"
            f"Apalancamiento: {leverage_range}"
        )
        cards.append({"content": block, "color": color})
    
    # Pie con ID y botón volver
    footer = f"🔐 ID: {signal.get('_id', 'N/A')}"
    
    return header, cards, footer


def view_signals_button(user):
    """
    Función principal del botón 'Ver señales' para la web.
    """
    signals, error_message = get_latest_signals_for_user(user)
    
    if error_message:
        # Mostrar mensaje centrado
        show_message(error_message, center=True)
        return
    
    for signal in signals:
        header, cards, footer = render_signal_card(signal, user)
        
        # Mostrar bloque general
        show_card(header, color="#FFFFFF", center=True)
        
        # Mostrar bloques de niveles
        for card in cards:
            show_card(card["content"], color=card["color"], center=True)
        
        # Mostrar pie y botón de volver
        show_card(footer, color="#EEEEEE", center=True)
        add_back_button("Volver al menú")
    
    # Actualizar último acceso
    signals_collection().update_one(
        {"_id": signal["_id"]},
        {"$set": update_timestamp(user)}
  )
