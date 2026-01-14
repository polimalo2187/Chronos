import logging
import json
from typing import Optional
from pywebpush import webpush, WebPushException
from app.database import users_collection
import asyncio
import secrets

logger = logging.getLogger(__name__)

# ======================================================
# ENV VARIABLES / CONFIGURACIÓN
# ======================================================

VAPID_PUBLIC_KEY = "TU_VAPID_PUBLIC_KEY_AQUI"
VAPID_PRIVATE_KEY = "TU_VAPID_PRIVATE_KEY_AQUI"
VAPID_CLAIMS = {
    "sub": "mailto:tu_email@dominio.com"
}

# ======================================================
# ENVÍO DE NOTIFICACIÓN PUSH
# ======================================================

async def send_web_push(user_id: int, message: str) -> str:
    """
    Envía notificación push web a un usuario usando el token almacenado en DB.
    Retorna un alert_id único para manejar auto-delete.
    """
    users_col = users_collection()
    user = users_col.find_one({"user_id": user_id})

    if not user:
        logger.warning(f"Usuario {user_id} no encontrado para push web")
        return ""

    # token_web debe ser un diccionario JSON con "endpoint", "keys" (p256dh y auth)
    subscription = user.get("web_push_token")
    if not subscription:
        logger.warning(f"Usuario {user_id} no tiene token web válido")
        return ""

    alert_id = secrets.token_hex(6)  # ID único para esta alerta

    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({
                "alert_id": alert_id,
                "message": message
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        logger.info(f"✅ Push web enviado a {user_id}")
        return alert_id
    except WebPushException as e:
        logger.error(f"❌ Error enviando push web a {user_id}: {e}")
        return ""

# ======================================================
# ELIMINAR ALERTA (AUTO DELETE OPCIONAL)
# ======================================================

async def remove_web_push_alert(user_id: int, alert_id: str):
    """
    Opcional: envía notificación de "borrar alerta" o limpia cache en front-end.
    """
    # Depende de tu front-end; aquí solo se registra
    logger.debug(f"🗑️ Auto-delete alerta {alert_id} para usuario {user_id}")
    # En front-end se puede recibir alert_id y desaparecer notificación
    # Por ahora no hace nada más
    await asyncio.sleep(0)  # Mantener async
