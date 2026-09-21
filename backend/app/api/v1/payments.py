"""
Bangladesh payment adapters.
COD is fully implemented. bKash / Nagad / Rocket are structured
for official merchant API integration (credentials via env).
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from bson import ObjectId

from app.core.database import get_db
from app.core.config import settings
from app.core.constants import PaymentMethod, PaymentStatus
from app.api.deps import get_current_customer, require_permission
from app.services.audit_service import log_action
from app.services.invoice_service import regenerate_order_invoice

router = APIRouter(prefix="/payments", tags=["Payments"])


def _to_oid(value: str, label: str = "id"):
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {label}")


class PaymentInit(BaseModel):
    order_id: str
    method: PaymentMethod
    amount: float
    customer_phone: Optional[str] = None


class PaymentCallback(BaseModel):
    transaction_id: str
    order_id: str
    status: str
    amount: Optional[float] = None
    raw: Optional[dict] = None


# ---------- Common interface ----------
class PaymentProvider:
    async def initiate(self, order: dict, amount: float, phone: str = None) -> dict:
        raise NotImplementedError

    async def verify(self, transaction_id: str) -> dict:
        raise NotImplementedError


class CODProvider(PaymentProvider):
    async def initiate(self, order: dict, amount: float, phone: str = None) -> dict:
        return {
            "provider": "cod",
            "status": "cod_pending",
            "message": "Cash on Delivery selected. Collect ৳{:.2f} on delivery.".format(amount),
            "amount": amount,
        }


class BKashProvider(PaymentProvider):
    async def initiate(self, order: dict, amount: float, phone: str = None) -> dict:
        # Production: call bKash Create Payment API with settings.BKASH_* credentials
        if not settings.BKASH_API_KEY:
            return {
                "provider": "bkash",
                "status": "sandbox_stub",
                "message": "bKash credentials not configured. Set BKASH_API_KEY etc.",
                "sandbox": True,
                "amount": amount,
                "order_id": str(order["_id"]),
            }
        # Real integration would:
        # 1. Get token from bKash
        # 2. Create payment
        # 3. Return paymentID + redirect URL
        return {
            "provider": "bkash",
            "status": "initiated",
            "payment_id": f"bkash_stub_{order['order_number']}",
            "redirect_url": f"{settings.FRONTEND_URL}/payment/bkash/return",
            "amount": amount,
        }


class NagadProvider(PaymentProvider):
    async def initiate(self, order: dict, amount: float, phone: str = None) -> dict:
        if not settings.NAGAD_MERCHANT_ID:
            return {
                "provider": "nagad",
                "status": "sandbox_stub",
                "message": "Nagad credentials not configured",
                "amount": amount,
            }
        return {
            "provider": "nagad",
            "status": "initiated",
            "payment_id": f"nagad_stub_{order['order_number']}",
            "amount": amount,
        }


class RocketProvider(PaymentProvider):
    async def initiate(self, order: dict, amount: float, phone: str = None) -> dict:
        return {
            "provider": "rocket",
            "status": "sandbox_stub",
            "message": "Rocket integration placeholder",
            "amount": amount,
        }


PROVIDERS = {
    PaymentMethod.COD: CODProvider(),
    PaymentMethod.BKASH: BKashProvider(),
    PaymentMethod.NAGAD: NagadProvider(),
    PaymentMethod.ROCKET: RocketProvider(),
}


@router.post("/initiate")
async def initiate_payment(
    body: PaymentInit,
    customer: dict = Depends(get_current_customer),
):
    db = get_db()
    order = await db.orders.find_one({"_id": _to_oid(body.order_id), "customer_id": ObjectId(customer["id"])})
    if not order:
        raise HTTPException(404, "Order not found")
    if abs(order["total"] - body.amount) > 0.01:
        raise HTTPException(400, "Amount mismatch")

    provider = PROVIDERS.get(body.method)
    if not provider:
        raise HTTPException(400, "Unsupported payment method")

    result = await provider.initiate(order, body.amount, body.customer_phone)

    await db.payments.insert_one({
        "order_id": order["_id"],
        "method": body.method,
        "amount": body.amount,
        "status": result.get("status", "pending"),
        "provider_response": result,
        "created_at": datetime.now(timezone.utc),
    })
    return result


@router.post("/{provider}/callback")
async def payment_callback(provider: str, body: PaymentCallback, request: Request):
    """Called by payment gateway or frontend after redirect."""
    db = get_db()
    order = await db.orders.find_one({"_id": _to_oid(body.order_id)})
    if not order:
        raise HTTPException(404, "Order not found")

    status = PaymentStatus.PAID if body.status in ("success", "completed", "paid") else PaymentStatus.FAILED
    await db.orders.update_one(
        {"_id": order["_id"]},
        {
            "$set": {
                "payment_status": status,
                "payment_transaction_id": body.transaction_id,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    await db.payments.update_one(
        {"order_id": order["_id"]},
        {"$set": {"status": status, "transaction_id": body.transaction_id, "callback": body.model_dump()}},
        upsert=True,
    )
    await log_action(None, "system", "payment.callback", "order", body.order_id, {"status": status, "provider": provider})
    await regenerate_order_invoice(str(order["_id"]))
    return {"message": "Callback processed", "payment_status": status}


@router.get("/admin/cod")
async def list_cod_orders(
    status: Optional[str] = None,
    admin: dict = Depends(require_permission("orders.view")),
):
    db = get_db()
    filt = {"payment_method": PaymentMethod.COD}
    if status:
        filt["payment_status"] = status
    cursor = db.orders.find(filt).sort("created_at", -1).limit(100)
    return [
        {
            "id": str(o["_id"]),
            "order_number": o.get("order_number"),
            "total": o.get("total"),
            "payment_status": o.get("payment_status"),
            "status": o.get("status"),
            "address": o.get("shipping_address"),
        }
        async for o in cursor
    ]