from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException
from starlette.responses import RedirectResponse

router = APIRouter()

# Permite letras/números y - _ . (códigos tipo: AB12cd, carlos_2026, promo-01)
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate_code(code: str) -> str:
    code = (code or "").strip()
    if not _CODE_RE.match(code):
        raise HTTPException(status_code=404, detail="Invalid referral code")
    return code


@router.get("/referrals/{code}", include_in_schema=False)
def open_referral(code: str):
    """
    Link público de referidos.
    - Guarda cookie con el referral_code
    - Redirige al home del frontend (SPA) con ?ref=CODE
    """
    code = _validate_code(code)

    resp = RedirectResponse(url=f"/?ref={code}", status_code=302)
    # cookie para que el frontend pueda leerlo incluso si no usa querystring
    resp.set_cookie(
        key="referral_code",
        value=code,
        max_age=60 * 60 * 24 * 30,  # 30 días
        path="/",
        httponly=False,   # lo necesita el frontend
        samesite="lax",
        secure=True,
    )
    return resp


# Alias por si alguien usa singular: /referral/{code}
@router.get("/referral/{code}", include_in_schema=False)
def open_referral_alias(code: str):
    return open_referral(code)
