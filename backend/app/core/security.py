from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import secrets
import pyotp
import qrcode
import io
import base64
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str,
    token_type: str = "customer",  # "customer" | "admin"
    extra: Optional[dict] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    if expires_minutes is None:
        expires_minutes = (
            settings.ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES
            if token_type == "admin"
            else settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    token_type: str = "customer",
    expires_days: Optional[int] = None,
) -> str:
    if expires_days is None:
        expires_days = (
            settings.ADMIN_REFRESH_TOKEN_EXPIRE_DAYS
            if token_type == "admin"
            else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    payload = {
        "sub": subject,
        "type": token_type,
        "token_use": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# ---------- TOTP 2FA ----------
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.provisioning_uri(name=email, issuer_name=settings.TOTP_ISSUER)


def generate_qr_base64(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret, digits=settings.TOTP_DIGITS, interval=settings.TOTP_INTERVAL)
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4).upper() for _ in range(count)]


def hash_backup_code(code: str) -> str:
    return pwd_context.hash(code)


def verify_backup_code(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)