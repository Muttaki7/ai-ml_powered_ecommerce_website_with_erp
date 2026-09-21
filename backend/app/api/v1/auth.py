from fastapi import APIRouter, Depends, Request
from app.schemas.auth import (
    CustomerRegister, CustomerLogin, AdminLogin, Admin2FAVerify,
    Admin2FASetupConfirm, TokenResponse, AdminLoginChallenge,
    RefreshRequest, MessageResponse,
)
from app.services import auth_service
from app.services.admin_service import get_admin
from app.api.deps import get_current_admin, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------- Admin profile ----------
@router.get("/admin/me")
async def admin_me(admin: dict = Depends(get_current_admin)):
    """Return the authenticated admin's profile. Only admin tokens pass here."""
    return await get_admin(admin["id"])


# ---------- Customer ----------
@router.post("/customer/register", response_model=dict)
async def customer_register(body: CustomerRegister, request: Request):
    ip = get_client_ip(request)
    user = await auth_service.register_customer(body.model_dump(), ip=ip)
    return {"message": "Registered successfully", "user": user}


@router.post("/customer/login", response_model=TokenResponse)
async def customer_login(body: CustomerLogin, request: Request):
    ip = get_client_ip(request)
    return await auth_service.login_customer(body.email, body.password, ip=ip)


@router.post("/customer/refresh", response_model=TokenResponse)
async def customer_refresh(body: RefreshRequest):
    return await auth_service.refresh_tokens(body.refresh_token)


@router.post("/customer/logout", response_model=MessageResponse)
async def customer_logout():
    # Client discards tokens; optionally blacklist refresh jti
    return {"message": "Logged out", "success": True}


# ---------- Admin ----------
@router.post("/admin/login")
async def admin_login(body: AdminLogin, request: Request):
    """
    Returns either full tokens (if 2FA not required / not enabled)
    or a 2FA challenge with temp_token.
    """
    ip = get_client_ip(request)
    result = await auth_service.login_admin_password(body.email, body.password, ip=ip)
    return result


@router.post("/admin/2fa/verify", response_model=TokenResponse)
async def admin_2fa_verify(body: Admin2FAVerify, request: Request):
    ip = get_client_ip(request)
    return await auth_service.verify_admin_2fa(body.email, body.code, ip=ip)


@router.post("/admin/2fa/setup")
async def admin_2fa_setup(admin: dict = Depends(get_current_admin)):
    return await auth_service.setup_admin_2fa(admin["id"])


@router.post("/admin/2fa/confirm", response_model=MessageResponse)
async def admin_2fa_confirm(
    body: Admin2FASetupConfirm,
    admin: dict = Depends(get_current_admin),
):
    return await auth_service.confirm_admin_2fa(admin["id"], body.code)


@router.post("/admin/refresh", response_model=TokenResponse)
async def admin_refresh(body: RefreshRequest):
    return await auth_service.refresh_tokens(body.refresh_token)


@router.post("/admin/logout", response_model=MessageResponse)
async def admin_logout():
    return {"message": "Logged out", "success": True}