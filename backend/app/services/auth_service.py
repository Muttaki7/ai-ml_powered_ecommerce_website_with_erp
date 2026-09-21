from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_totp_secret, get_totp_uri, generate_qr_base64,
    verify_totp, generate_backup_codes, hash_backup_code, verify_backup_code,
)
from app.core.config import settings
from app.core.constants import ROLE_PERMISSIONS, AdminRole, UserStatus
from app.services.audit_service import log_action


# ---------- Customer Auth ----------
async def register_customer(data: dict, ip: str = None) -> dict:
    db = get_db()
    existing = await db.customers.find_one({"email": data["email"].lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "full_name": data["full_name"],
        "email": data["email"].lower(),
        "phone": data["phone"],
        "password_hash": hash_password(data["password"]),
        "status": UserStatus.ACTIVE,
        "addresses": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db.customers.insert_one(doc)
    customer_id = str(result.inserted_id)
    await log_action(customer_id, "customer", "customer.register", "customer", customer_id, ip=ip)
    return await get_customer_safe(customer_id)


async def login_customer(email: str, password: str, ip: str = None) -> dict:
    db = get_db()
    user = await db.customers.find_one({"email": email.lower()})
    if not user or not verify_password(password, user["password_hash"]):
        await log_action(None, "customer", "customer.login_failed", details={"email": email}, ip=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("status") != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account disabled")

    access = create_access_token(str(user["_id"]), "customer")
    refresh = create_refresh_token(str(user["_id"]), "customer")
    await _store_refresh(str(user["_id"]), "customer", refresh)
    await log_action(str(user["_id"]), "customer", "customer.login", ip=ip)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _serialize_customer(user),
    }


# ---------- Admin Auth ----------
async def login_admin_password(email: str, password: str, ip: str = None) -> dict:
    """Step 1: validate password. If 2FA required, return challenge."""
    db = get_db()
    admin = await db.admins.find_one({"email": email.lower()})
    if not admin:
        await log_action(None, "admin", "admin.login_failed", details={"email": email}, ip=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Lockout check
    if admin.get("lockout_until") and admin["lockout_until"] > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")

    if not verify_password(password, admin["password_hash"]):
        fails = admin.get("failed_login_attempts", 0) + 1
        update = {"failed_login_attempts": fails}
        if fails >= settings.MAX_2FA_ATTEMPTS:
            update["lockout_until"] = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_MINUTES)
        await db.admins.update_one({"_id": admin["_id"]}, {"$set": update})
        await log_action(str(admin["_id"]), "admin", "admin.login_failed", ip=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Reset failed attempts
    await db.admins.update_one(
        {"_id": admin["_id"]},
        {"$set": {"failed_login_attempts": 0, "lockout_until": None}},
    )

    # Check 2FA
    two_factor = admin.get("two_factor") or {}
    if admin.get("two_factor_required", True) and two_factor.get("enabled"):
        # Issue short-lived temp token for 2FA step
        temp = create_access_token(
            str(admin["_id"]),
            "admin",
            extra={"2fa_pending": True},
            expires_minutes=5,
        )
        return {
            "requires_2fa": True,
            "message": "Two-factor authentication required",
            "email": admin["email"],
            "temp_token": temp,
        }

    # No 2FA or not yet enrolled → issue full tokens (but force setup later)
    return await _issue_admin_tokens(admin, ip)


async def verify_admin_2fa(email: str, code: str, ip: str = None) -> dict:
    db = get_db()
    admin = await db.admins.find_one({"email": email.lower()})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid request")

    two_factor = admin.get("two_factor") or {}
    if not two_factor.get("enabled") or not two_factor.get("secret"):
        raise HTTPException(status_code=400, detail="2FA not configured")

    # Rate-limit style lockout already handled at password stage
    if not verify_totp(two_factor["secret"], code):
        # Try backup codes
        backup_ok = False
        for i, hashed in enumerate(two_factor.get("backup_codes") or []):
            if verify_backup_code(code, hashed):
                # Invalidate used backup code
                codes = two_factor["backup_codes"]
                codes.pop(i)
                await db.admins.update_one(
                    {"_id": admin["_id"]},
                    {"$set": {"two_factor.backup_codes": codes}},
                )
                backup_ok = True
                break
        if not backup_ok:
            await log_action(str(admin["_id"]), "admin", "admin.2fa_failed", ip=ip)
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    await log_action(str(admin["_id"]), "admin", "admin.2fa_success", ip=ip)
    return await _issue_admin_tokens(admin, ip)


async def setup_admin_2fa(admin_id: str) -> dict:
    db = get_db()
    admin = await db.admins.find_one({"_id": ObjectId(admin_id)})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    secret = generate_totp_secret()
    uri = get_totp_uri(secret, admin["email"])
    qr = generate_qr_base64(uri)
    backup = generate_backup_codes()

    # Store secret temporarily (not enabled until confirmed)
    await db.admins.update_one(
        {"_id": admin["_id"]},
        {
            "$set": {
                "two_factor": {
                    "secret": secret,
                    "enabled": False,
                    "backup_codes": [hash_backup_code(c) for c in backup],
                    "pending": True,
                }
            }
        },
    )
    return {
        "secret": secret,
        "qr_code_base64": qr,
        "otpauth_uri": uri,
        "backup_codes": backup,  # show once
        "message": "Scan QR with authenticator app, then confirm with a code",
    }


async def confirm_admin_2fa(admin_id: str, code: str) -> dict:
    db = get_db()
    admin = await db.admins.find_one({"_id": ObjectId(admin_id)})
    if not admin or not admin.get("two_factor", {}).get("secret"):
        raise HTTPException(status_code=400, detail="No pending 2FA setup")

    if not verify_totp(admin["two_factor"]["secret"], code):
        raise HTTPException(status_code=400, detail="Invalid code")

    await db.admins.update_one(
        {"_id": admin["_id"]},
        {"$set": {"two_factor.enabled": True, "two_factor.pending": False}},
    )
    await log_action(admin_id, "admin", "admin.2fa_enrolled")
    return {"message": "2FA enabled successfully", "success": True}


async def _issue_admin_tokens(admin: dict, ip: str = None) -> dict:
    perms = admin.get("permissions") or ROLE_PERMISSIONS.get(admin.get("role"), [])
    if admin.get("is_main_admin"):
        perms = ROLE_PERMISSIONS[AdminRole.MAIN_ADMIN]

    access = create_access_token(
        str(admin["_id"]),
        "admin",
        extra={
            "role": admin.get("role"),
            "permissions": perms,
            "is_main_admin": admin.get("is_main_admin", False),
        },
    )
    refresh = create_refresh_token(str(admin["_id"]), "admin")
    await _store_refresh(str(admin["_id"]), "admin", refresh)
    await log_action(str(admin["_id"]), "admin", "admin.login", ip=ip)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _serialize_admin(admin),
    }


async def _store_refresh(user_id: str, token_type: str, token: str) -> None:
    db = get_db()
    payload = decode_token(token)
    if not payload:
        return
    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "token_type": token_type,
        "token_jti": payload["jti"],
        "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        "created_at": datetime.now(timezone.utc),
    })


async def refresh_tokens(refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if not payload or payload.get("token_use") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db = get_db()
    stored = await db.refresh_tokens.find_one({"token_jti": payload["jti"]})
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    token_type = payload["type"]
    user_id = payload["sub"]

    if token_type == "admin":
        admin = await db.admins.find_one({"_id": ObjectId(user_id)})
        if not admin or admin.get("status") != "active":
            raise HTTPException(status_code=401, detail="Admin inactive")
        # revoke old
        await db.refresh_tokens.delete_one({"token_jti": payload["jti"]})
        return await _issue_admin_tokens(admin)
    else:
        user = await db.customers.find_one({"_id": ObjectId(user_id)})
        if not user or user.get("status") != UserStatus.ACTIVE:
            raise HTTPException(status_code=401, detail="User inactive")
        await db.refresh_tokens.delete_one({"token_jti": payload["jti"]})
        access = create_access_token(user_id, "customer")
        new_refresh = create_refresh_token(user_id, "customer")
        await _store_refresh(user_id, "customer", new_refresh)
        return {
            "access_token": access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": _serialize_customer(user),
        }


def _serialize_customer(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "status": user.get("status"),
    }


def _serialize_admin(admin: dict) -> dict:
    two_factor = admin.get("two_factor") or {}
    perms = admin.get("permissions") or ROLE_PERMISSIONS.get(admin.get("role"), [])
    if admin.get("is_main_admin"):
        perms = ROLE_PERMISSIONS[AdminRole.MAIN_ADMIN]
    return {
        "id": str(admin["_id"]),
        "full_name": admin.get("full_name") or admin.get("name"),
        "email": admin.get("email"),
        "phone": admin.get("phone"),
        "role": admin.get("role"),
        "permissions": perms,
        "is_main_admin": admin.get("is_main_admin", False),
        "two_factor_enabled": bool(two_factor.get("enabled")),
        "two_factor_required": admin.get("two_factor_required", True),
        "status": admin.get("status"),
    }


async def get_customer_safe(customer_id: str) -> dict:
    db = get_db()
    user = await db.customers.find_one({"_id": ObjectId(customer_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _serialize_customer(user)