from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/referrals/{code}", include_in_schema=False)
async def referral_landing(code: str):
    """
    Public landing for referral links.

    This simply redirects into the SPA (/) carrying the referral code as a query param.
    Your frontend can read ?ref=... and store it (localStorage) until the user registers.

    Example:
      https://<domain>/referrals/ABC123  ->  https://<domain>/?ref=ABC123
    """
    safe_code = (code or "").strip()
    return RedirectResponse(url=f"/?ref={safe_code}", status_code=307)

@router.get("/referral/{code}", include_in_schema=False)
async def referral_landing_alias(code: str):
    # Backwards-compatible alias
    safe_code = (code or "").strip()
    return RedirectResponse(url=f"/?ref={safe_code}", status_code=307)
