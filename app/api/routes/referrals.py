from fastapi import APIRouter
from starlette.responses import RedirectResponse


router = APIRouter()


@router.get("/{code}")
async def referral_redirect(code: str):
    """Link público de referidos.

    Uso:
      https://TU_DOMINIO/referrals/ABC12345

    La UI captura el querystring ?ref=... y lo guarda para el registro.
    """
    # Redirigimos a la portada/app con el parámetro ref
    url = f"/?ref={code}"
    return RedirectResponse(url=url, status_code=307)
