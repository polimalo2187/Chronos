import asyncio
import logging
from typing import List, Dict
from datetime import datetime

from app.database import users_collection
from app.plans import PLAN_FREE, PLAN_PLUS, PLAN_PREMIUM
from app.config import is_admin
from app.models import is_trial_active, is_plan_active
from app.webpush import send_web_push  # Nueva función para notificaciones web

logger = logging.getLogger(__name__)

# ======================================================
# CONFIGURACIÓN
# ======================================================

ALERT_AUTO_DELETE_SECONDS = 8  # Solo para mostrar temporal en la web (opcional)

# ======================================================
# USUARIOS ELEGIBLES POR PLAN
# ======================================================

def _eligible_users_for_alert(signal_visibility: str) -> List[int]:
    """
    Retorna usuarios que DEBEN recibir el push.
    Reglas:
    - Cada usuario SOLO recibe push de su plan
    - Admin SOLO recibe PREMIUM
    """

    users_col = users_collection()
    eligible_users: List[int] = []

    users = users_col.find(
        {},
        {"user_id": 1, "plan": 1, "trial_end": 1, "plan_end": 1}
    )

    for user in users:
        user_id = user.get("user_id")
        user_plan = user.get("plan", PLAN_FREE)

        admin = is_admin(user_id)
        has_access = is_plan_active(user) or is_trial_active(user)

        if not has_access and not admin:
            continue

        if admin:
            if signal_visibility == PLAN_PREMIUM:
                eligible_users.append(user_id)
            continue

        if user_plan == signal_visibility:
            eligible_users.append(user_id)

    return eligible_users

# ======================================================
# AUTO DELETE (opcional en web)
# ======================================================

async def _auto_delete_web(user_id: int, alert_id: str):
    await asyncio.sleep(ALERT_AUTO_DELETE_SECONDS)
    try:
        from app.webpush import remove_web_push_alert
        await remove_web_push_alert(user_id, alert_id)
    except Exception:
        pass

# ======================================================
# PUSH DE NUEVA SEÑAL (VERSIÓN WEB)
# ======================================================

async def notify_new_signal_alert(signal_visibility: str, **kwargs):
    """
    Envía push web inmediatamente cuando hay señal.
    Filtrado SOLO por plan exacto.
    """

    user_ids = _eligible_users_for_alert(signal_visibility)

    if not user_ids:
        logger.warning(f"📭 Push NO enviado: sin usuarios para plan {signal_visibility}")
        return

    alert_text = (
        "📢 NUEVA SEÑAL DISPONIBLE\n\n"
        "👉 Abre la web para ver detalles.\n\n"
        "⏳ Tiempo limitado."
    )

    sent = 0

    for user_id in user_ids:
        try:
            # send_web_push maneja el token web almacenado en DB
            alert_id = await send_web_push(user_id, alert_text)
            # Auto delete opcional
            asyncio.create_task(_auto_delete_web(user_id, alert_id))
            sent += 1
        except Exception as e:
            logger.warning(f"⚠️ Push web fallido a {user_id}: {e}")

    logger.info(f"📨 Push web enviado ({signal_visibility}): {sent}/{len(user_ids)} usuarios")

# ======================================================
# NOTIFICACIONES DE PLAN (VERSIÓN WEB)
# ======================================================

async def notify_plan_activation(user_id: int, plan: str, expires_at: datetime):
    try:
        text = f"✅ Plan {plan.upper()} activado.\nVence el: {expires_at.strftime('%d/%m/%Y')}"
        await send_web_push(user_id, text)
    except Exception as e:
        logger.error(f"❌ Error notificando activación a {user_id}: {e}")

async def notify_plan_expired(user_id: int):
    try:
        text = "⚠️ Tu plan ha expirado.\nContacta a un administrador para renovarlo."
        await send_web_push(user_id, text)
    except Exception as e:
        logger.error(f"❌ Error notificando expiración a {user_id}: {e}")
