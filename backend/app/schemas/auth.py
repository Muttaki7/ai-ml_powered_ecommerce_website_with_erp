from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class CustomerRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_bd_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^(?:\+880|880|0)?1[3-9]\d{8}$", v):
            raise ValueError("Invalid Bangladesh phone number")
        if v.startswith("+880"):
            v = "0" + v[4:]
        elif v.startswith("880"):
            v = "0" + v[3:]
        return v


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class Admin2FAVerify(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class Admin2FASetupConfirm(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class AdminLoginChallenge(BaseModel):
    """Returned when password is valid but 2FA is required."""
    requires_2fa: bool = True
    message: str = "Two-factor authentication required"
    email: str
    temp_token: Optional[str] = None  # short-lived token for 2FA step


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
    success: bool = True