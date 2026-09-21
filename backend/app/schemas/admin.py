from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import AdminRole


class AdminCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    temporary_password: str = Field(..., min_length=8)
    role: AdminRole
    permissions: Optional[List[str]] = None  # override role defaults
    two_factor_required: bool = True
    status: str = "active"


class AdminUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[AdminRole] = None
    permissions: Optional[List[str]] = None
    two_factor_required: Optional[bool] = None
    status: Optional[str] = None


class AdminOut(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    permissions: List[str]
    two_factor_required: bool
    two_factor_enabled: bool
    is_main_admin: bool
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RoleAssign(BaseModel):
    role: AdminRole
    permissions: Optional[List[str]] = None