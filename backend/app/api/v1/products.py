from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import aiofiles
from fastapi import APIRouter, Depends, Query, HTTPException, Request, UploadFile, File
from bson import ObjectId


from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, CategoryCreate, CategoryOut
from app.api.deps import get_current_admin, require_permission, get_current_customer
from app.core.constants import StockStatus

router = APIRouter(tags=["Products & Categories"])


def _to_oid(value: str, label: str = "id"):
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {label}")


def _slug(text: str) -> str:
    try:
        from slugify import slugify
        return slugify(text)
    except Exception:
        return text.lower().replace(" ", "-")[:80]


def _serialize_product(p: dict) -> dict:
    final = p.get("selling_price", 0) * (1 - p.get("discount_percent", 0) / 100)
    stock = p.get("stock_quantity", 0)
    min_s = p.get("min_stock_level", 5)
    if stock <= 0:
        status = StockStatus.OUT_OF_STOCK
    elif stock <= min_s:
        status = StockStatus.LOW_STOCK
    else:
        status = StockStatus.IN_STOCK
    return {
        "id": str(p["_id"]),
        "name": p.get("name"),
        "slug": p.get("slug"),
        "sku": p.get("sku"),
        "barcode": p.get("barcode"),
        "description": p.get("description"),
        "specifications": p.get("specifications"),
        "category_id": str(p.get("category_id")) if p.get("category_id") else None,
        "brand": p.get("brand"),
        "purchase_price": p.get("purchase_price", 0),
        "selling_price": p.get("selling_price", 0),
        "discount_percent": p.get("discount_percent", 0),
        "tax_percent": p.get("tax_percent", 0),
        "final_price": round(final, 2),
        "stock_quantity": stock,
        "min_stock_level": min_s,
        "available_stock": max(0, stock - p.get("reserved", 0)),
        "stock_status": status,
        "supplier_id": str(p["supplier_id"]) if p.get("supplier_id") else None,
        "images": p.get("images") or [],
        "variants": p.get("variants") or [],
        "tags": p.get("tags") or [],
        "is_featured": p.get("is_featured", False),
        "is_best_seller": p.get("is_best_seller", False),
        "status": p.get("status", "active"),
        "intelligence_score": p.get("intelligence_score"),
        "demand_trend": p.get("demand_trend"),
        "predicted_demand_30d": p.get("predicted_demand_30d"),
        "created_at": p.get("created_at").isoformat() if p.get("created_at") else None,
    }


# ---------- Public / Customer product listing ----------
@router.get("/products", response_model=List[dict])
async def list_products(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    best_seller: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
):
    db = get_db()
    filt: dict = {"status": "active"}
    if q:
        filt["$text"] = {"$search": q}
    if category_id:
        filt["category_id"] = _to_oid(category_id, "category id")
    if brand:
        filt["brand"] = brand
    if min_price is not None or max_price is not None:
        price_f = {}
        if min_price is not None:
            price_f["$gte"] = min_price
        if max_price is not None:
            price_f["$lte"] = max_price
        filt["selling_price"] = price_f
    if featured is not None:
        filt["is_featured"] = featured
    if best_seller is not None:
        filt["is_best_seller"] = best_seller

    cursor = db.products.find(filt).skip(skip).limit(limit).sort("created_at", -1)
    return [_serialize_product(p) async for p in cursor]


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    db = get_db()
    p = await db.products.find_one({"_id": _to_oid(product_id)})
    if not p:
        raise HTTPException(404, "Product not found")
    return _serialize_product(p)


# ---------- Admin product management ----------
@router.post("/admin/products", response_model=dict)
async def create_product(
    body: ProductCreate,
    admin: dict = Depends(require_permission("products.create")),
):
    db = get_db()
    if await db.products.find_one({"sku": body.sku}):
        raise HTTPException(400, "SKU already exists")
    doc = body.model_dump()
    doc["slug"] = doc.get("slug") or _slug(doc["name"])
    doc["category_id"] = _to_oid(doc["category_id"], "category id")
    if doc.get("supplier_id"):
        doc["supplier_id"] = _to_oid(doc["supplier_id"], "supplier id")
    doc["reserved"] = 0
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = doc["created_at"]
    result = await db.products.insert_one(doc)
    # also seed inventory
    await db.inventory.insert_one({
        "product_id": result.inserted_id,
        "warehouse_id": None,
        "quantity": doc["stock_quantity"],
        "reserved": 0,
        "min_level": doc["min_stock_level"],
        "updated_at": datetime.now(timezone.utc),
    })
    p = await db.products.find_one({"_id": result.inserted_id})
    return _serialize_product(p)


@router.patch("/admin/products/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    admin: dict = Depends(require_permission("products.edit")),
):
    db = get_db()
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if "category_id" in update:
        update["category_id"] = _to_oid(update["category_id"], "category id")
    update["updated_at"] = datetime.now(timezone.utc)
    result = await db.products.update_one({"_id": _to_oid(product_id)}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Product not found")
    p = await db.products.find_one({"_id": ObjectId(product_id)})
    return _serialize_product(p)


@router.delete("/admin/products/{product_id}")
async def delete_product(
    product_id: str,
    admin: dict = Depends(require_permission("products.delete")),
):
    db = get_db()
    result = await db.products.update_one(
        {"_id": _to_oid(product_id)},
        {"$set": {"status": "deleted", "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return {"message": "Product deleted", "success": True}


# ---------- Product image upload ----------
UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads" / "products"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@router.post("/admin/products/upload-image")
async def upload_product_image(
    request: Request,
    file: UploadFile = File(...),
    admin: dict = Depends(require_permission("products.create")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, WEBP or GIF images are allowed")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image exceeds the 5 MB limit")
    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    name = f"{uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(UPLOAD_DIR / name, "wb") as fh:
        await fh.write(data)
    base = str(request.base_url).rstrip("/")
    return {"url": f"{base}/uploads/products/{name}", "filename": name}


# ---------- Categories ----------
@router.get("/categories", response_model=List[dict])
async def list_categories():
    db = get_db()
    cats = [c async for c in db.categories.find({"status": "active"}).sort("order", 1)]
    # build tree
    by_id = {str(c["_id"]): {**c, "id": str(c["_id"]), "children": []} for c in cats}
    roots = []
    for c in by_id.values():
        pid = str(c.get("parent_id")) if c.get("parent_id") else None
        if pid and pid in by_id:
            by_id[pid]["children"].append(c)
        else:
            roots.append(c)
    def clean(node):
        return {
            "id": node["id"],
            "name": node.get("name"),
            "slug": node.get("slug"),
            "parent_id": str(node["parent_id"]) if node.get("parent_id") else None,
            "description": node.get("description"),
            "image": node.get("image"),
            "order": node.get("order", 0),
            "status": node.get("status"),
            "children": [clean(ch) for ch in node.get("children", [])],
        }
    return [clean(r) for r in roots]


@router.post("/admin/categories")
async def create_category(
    body: CategoryCreate,
    admin: dict = Depends(require_permission("categories.create")),
):
    db = get_db()
    doc = body.model_dump()
    doc["slug"] = doc.get("slug") or _slug(doc["name"])
    if doc.get("parent_id"):
        doc["parent_id"] = ObjectId(doc["parent_id"])
    doc["created_at"] = datetime.now(timezone.utc)
    result = await db.categories.insert_one(doc)
    return {"id": str(result.inserted_id), **body.model_dump()}