# web_ui_plans.py
from web_ui_framework import Card, CardContent, Button, CenteredContainer

from app.config import get_admin_whatsapps

# ======================================================
# FUNCIONES AUXILIARES
# ======================================================

def format_whatsapp_contacts() -> str:
    """
    Retorna los contactos de WhatsApp para activar planes.
    """
    whatsapps = get_admin_whatsapps()
    if not whatsapps:
        return "WhatsApp: (no configurado)"
    if len(whatsapps) == 1:
        return f"WhatsApp: {whatsapps[0]}"
    return "WhatsApps:\n- " + "\n- ".join(whatsapps)

# ======================================================
# FUNCIÓN PRINCIPAL DEL BOTÓN PLANES
# ======================================================

def show_plans():
    """
    Muestra los planes disponibles en una tarjeta centrada en la pantalla.
    """

    whatsapp_text = format_whatsapp_contacts()

    card_content = [
        ("🟢 FREE", "Prueba de 7 días"),
        ("🟡 PLUS", "Precio 5 USDT"),
        ("🔴 PREMIUM", "Precio 10 USDT"),
    ]

    # Crear tarjeta
    card = Card(
        title="💼 PLANES DISPONIBLES",
        content=[
            CardContent(text=f"{plan}: {desc}") for plan, desc in card_content
        ] + [
            CardContent(text="\n" + whatsapp_text)
        ],
        buttons=[
            Button(label="⬅️ Volver", action="back_to_menu")
        ]
    )

    # Mostrar centrado
    return CenteredContainer(content=card)
