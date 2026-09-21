from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import require_permission

router = APIRouter(tags=["Settings"])

CORE_ID = "core"

DEFAULT_SETTINGS: dict = {
    "banner": {
        "badge": "AI-powered pricing & stock forecasting",
        "title": "Shop smarter across Bangladesh",
        "subtitle": (
            "Products from trusted sellers. Cash on Delivery, bKash & Nagad — "
            "delivered fast to every division."
        ),
    },
    "posters": [
        {"title": "Big Sale", "subtitle": "Up to 50% off electronics", "accent": "from-rose-500 to-orange-400", "visible": True},
        {"title": "Best Price", "subtitle": "Groceries at wholesale rates", "accent": "from-emerald-500 to-teal-400", "visible": True},
        {"title": "Free Delivery", "subtitle": "On orders above the set threshold", "accent": "from-sky-500 to-cyan-400", "visible": True},
        {"title": "New Arrivals", "subtitle": "Fresh collection every week", "accent": "from-indigo-500 to-violet-400", "visible": True},
    ],
    "delivery": {
        "inside_dhaka": 60.0,
        "outside_dhaka": 120.0,
        "free_delivery_enabled": True,
        "free_delivery_threshold": 1000.0,
    },
}


def _deep_merge(base: dict, updates: dict) -> dict:
    out = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _apply_defaults(doc: dict) -> dict:
    """Fill missing keys from defaults so the API always returns a complete object."""
    if not doc:
        return _deep_merge({}, DEFAULT_SETTINGS)
    merged = _deep_merge(DEFAULT_SETTINGS, doc)
    # posters should always have a fixed length for the storefront grid
    posters = merged.get("posters") or []
    if len(posters) < 4:
        for p in DEFAULT_SETTINGS["posters"][len(posters):]:
            posters.append(p)
    merged["posters"] = posters[:4]
    return merged


async def get_settings_doc() -> dict:
    db = get_db()
    doc = await db.site_settings.find_one({"_id": CORE_ID})
    doc.pop("_id", None) if doc else None
    return _apply_defaults(doc)


async def get_delivery_charge(subtotal: float, division: str) -> float:
    """Admin-configured delivery charge: Dhaka vs outside Dhaka, free above threshold."""
    s = await get_settings_doc()
    delivery = s.get("delivery") or {}
    threshold = float(delivery.get("free_delivery_threshold", 0) or 0)
    enabled = bool(delivery.get("free_delivery_enabled", False))
    if enabled and threshold > 0 and subtotal >= threshold:
        return 0.0
    is_dhaka = division.strip().lower() == "dhaka"
    if is_dhaka:
        return float(delivery.get("inside_dhaka", 0) or 0)
    return float(delivery.get("outside_dhaka", 0) or 0)


class BannerIn(BaseModel):
    badge: str = ""
    title: str = ""
    subtitle: str = ""


class PosterIn(BaseModel):
    title: str = ""
    subtitle: str = ""
    accent: str = "from-sky-500 to-indigo-600"
    visible: bool = True


class DeliveryIn(BaseModel):
    inside_dhaka: float = Field(0, ge=0)
    outside_dhaka: float = Field(0, ge=0)
    free_delivery_enabled: bool = False
    free_delivery_threshold: float = Field(0, ge=0)


class SettingsUpdate(BaseModel):
    banner: Optional[BannerIn] = None
    posters: Optional[List[PosterIn]] = None
    delivery: Optional[DeliveryIn] = None


@router.get("/settings/public")
async def public_settings():
    """Public storefront settings (banner, posters, delivery charges)."""
    return await get_settings_doc()


@router.get("/admin/settings")
async def admin_get_settings(
    admin: dict = Depends(require_permission("settings.view")),
):
    return await get_settings_doc()


@router.put("/admin/settings")
async def admin_update_settings(
    body: SettingsUpdate,
    admin: dict = Depends(require_permission("settings.edit")),
):
    db = get_db()
    current = await get_settings_doc()
    update = body.model_dump(exclude_none=True)
    merged = _deep_merge(current, update)
    merged["updated_by"] = admin["id"]
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.site_settings.replace_one(
        {"_id": CORE_ID},
        {**merged, "_id": CORE_ID},
        upsert=True,
    )
    return _apply_defaults(merged)