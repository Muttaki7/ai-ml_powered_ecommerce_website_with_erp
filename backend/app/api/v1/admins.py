from typing import List
from fastapi import APIRouter, Depends, Query
from app.schemas.admin import AdminCreate, AdminUpdate, AdminOut, RoleAssign
from app.services import admin_service
from app.api.deps import get_current_admin, require_permission

router = APIRouter(prefix="/admins", tags=["Administrators"])


@router.get("", response_model=List[AdminOut])
async def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: dict = Depends(require_permission("admins.view")),
):
    return await admin_service.list_admins(skip, limit)


@router.post("", response_model=AdminOut)
async def create_admin(
    body: AdminCreate,
    admin: dict = Depends(require_permission("admins.create")),
):
    return await admin_service.create_admin(
        body.model_dump(),
        creator_id=admin["id"],
        creator_is_main=admin.get("is_main_admin", False),
    )


@router.get("/{admin_id}", response_model=AdminOut)
async def get_admin(
    admin_id: str,
    admin: dict = Depends(require_permission("admins.view")),
):
    return await admin_service.get_admin(admin_id)


@router.patch("/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: str,
    body: AdminUpdate,
    admin: dict = Depends(require_permission("admins.edit")),
):
    return await admin_service.update_admin(
        admin_id,
        body.model_dump(exclude_unset=True),
        actor_id=admin["id"],
        actor_is_main=admin.get("is_main_admin", False),
    )


@router.post("/{admin_id}/disable")
async def disable_admin(
    admin_id: str,
    admin: dict = Depends(require_permission("admins.disable")),
):
    return await admin_service.disable_admin(
        admin_id, admin["id"], admin.get("is_main_admin", False)
    )


@router.post("/{admin_id}/2fa/reset")
async def reset_2fa(
    admin_id: str,
    admin: dict = Depends(require_permission("admins.edit")),
):
    return await admin_service.reset_admin_2fa(
        admin_id, admin["id"], admin.get("is_main_admin", False)
    )


@router.put("/{admin_id}/roles")
async def assign_role(
    admin_id: str,
    body: RoleAssign,
    admin: dict = Depends(require_permission("admins.assign_roles")),
):
    return await admin_service.update_admin(
        admin_id,
        {"role": body.role, "permissions": body.permissions},
        actor_id=admin["id"],
        actor_is_main=admin.get("is_main_admin", False),
    )