"""
Seed realistic Bangladesh demo data so ML & analytics dashboards show meaningful trends.
Run: cd backend && python -m scripts.seed   (or from repo root)
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.core.security import hash_password
from app.core.constants import ROLE_PERMISSIONS, AdminRole, OrderStatus, PaymentMethod, PaymentStatus

CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "children": ["Mobile Phones", "Laptops", "Accessories"]},
    {"name": "Fashion", "slug": "fashion", "children": ["Men's Clothing", "Women's Clothing", "Shoes"]},
    {"name": "Home & Living", "slug": "home-living", "children": ["Kitchen", "Furniture", "Decor"]},
    {"name": "Groceries", "slug": "groceries", "children": ["Rice & Flour", "Spices", "Snacks"]},
    {"name": "Beauty", "slug": "beauty", "children": ["Skincare", "Makeup"]},
]

PRODUCT_TEMPLATES = [
    ("Samsung Galaxy A55", "Electronics", "Mobile Phones", 32000, 38999, 45),
    ("Xiaomi Redmi Note 13", "Electronics", "Mobile Phones", 18000, 22999, 80),
    ("Walton Laptop i5", "Electronics", "Laptops", 45000, 54999, 25),
    ("Anker PowerBank 20000mAh", "Electronics", "Accessories", 1800, 2499, 120),
    ("Men's Cotton Panjabi", "Fashion", "Men's Clothing", 650, 999, 200),
    ("Women's Cotton Saree", "Fashion", "Women's Clothing", 1200, 1899, 150),
    ("Sports Shoes Unisex", "Fashion", "Shoes", 900, 1499, 90),
    ("Non-stick Fry Pan", "Home & Living", "Kitchen", 450, 799, 70),
    ("Miniket Rice 25kg", "Groceries", "Rice & Flour", 1800, 2150, 300),
    ("Pran Spicy Chanachur", "Groceries", "Snacks", 35, 55, 500),
    ("Himalaya Face Wash", "Beauty", "Skincare", 180, 299, 200),
    ("Maybelline Lipstick", "Beauty", "Makeup", 350, 550, 100),
]

DIVISIONS = ["Dhaka", "Chattogram", "Rajshahi", "Khulna", "Sylhet", "Rangpur"]
DISTRICTS = {
    "Dhaka": ["Dhaka", "Gazipur", "Narayanganj"],
    "Chattogram": ["Chattogram", "Cox's Bazar"],
    "Rajshahi": ["Rajshahi", "Bogura"],
    "Khulna": ["Khulna", "Jessore"],
    "Sylhet": ["Sylhet", "Moulvibazar"],
    "Rangpur": ["Rangpur", "Dinajpur"],
}


async def seed():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]

    print("Clearing existing demo collections...")
    for col in ["admins", "customers", "categories", "products", "orders", "inventory", "audit_logs", "payments"]:
        await db[col].delete_many({})

    # Main Admin
    main_admin = {
        "full_name": "Main Administrator",
        "email": "admin@example.com",
        "phone": "01700000001",
        "password_hash": hash_password("Admin@12345"),
        "role": AdminRole.MAIN_ADMIN,
        "permissions": ROLE_PERMISSIONS[AdminRole.MAIN_ADMIN],
        "two_factor_required": True,
        "two_factor": None,
        "is_main_admin": True,
        "status": "active",
        "failed_login_attempts": 0,
        "lockout_until": None,
        "must_change_password": False,
        "created_by": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.admins.insert_one(main_admin)
    print("Main Admin: admin@example.com / Admin@12345  (enable 2FA after first login)")

    # Inventory Manager example
    inv_admin = {
        "full_name": "Rahim Inventory",
        "email": "rahim@example.com",
        "phone": "01700000002",
        "password_hash": hash_password("Rahim@12345"),
        "role": AdminRole.INVENTORY_MANAGER,
        "permissions": ROLE_PERMISSIONS[AdminRole.INVENTORY_MANAGER],
        "two_factor_required": True,
        "two_factor": None,
        "is_main_admin": False,
        "status": "active",
        "failed_login_attempts": 0,
        "created_by": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.admins.insert_one(inv_admin)

    # Categories
    cat_map = {}  # name -> ObjectId
    for root in CATEGORIES:
        rdoc = {
            "name": root["name"],
            "slug": root["slug"],
            "parent_id": None,
            "order": 0,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
        r = await db.categories.insert_one(rdoc)
        cat_map[root["name"]] = r.inserted_id
        for i, child in enumerate(root["children"]):
            cdoc = {
                "name": child,
                "slug": child.lower().replace(" ", "-").replace("'", ""),
                "parent_id": r.inserted_id,
                "order": i,
                "status": "active",
                "created_at": datetime.now(timezone.utc),
            }
            c = await db.categories.insert_one(cdoc)
            cat_map[child] = c.inserted_id
    print(f"Categories: {len(cat_map)}")

    # Products
    product_ids = []
    for name, root_cat, sub_cat, purchase, sell, stock in PRODUCT_TEMPLATES:
        # create a few variants by slight price/stock variation
        for i in range(3 if "Phone" in name or "Laptop" in name else 1):
            p_name = name if i == 0 else f"{name} (Var {i+1})"
            sku = f"SKU-{abs(hash(p_name)) % 100000:05d}"
            doc = {
                "name": p_name,
                "slug": p_name.lower().replace(" ", "-")[:60],
                "sku": sku,
                "description": f"Quality {p_name} available across Bangladesh. Fast delivery.",
                "category_id": cat_map.get(sub_cat) or cat_map.get(root_cat),
                "brand": name.split()[0],
                "purchase_price": purchase + i * 100,
                "selling_price": sell + i * 150,
                "discount_percent": random.choice([0, 5, 10, 15]),
                "tax_percent": 0,
                "stock_quantity": stock - i * 5,
                "min_stock_level": max(5, stock // 10),
                "reserved": 0,
                "images": [],
                "variants": [],
                "tags": [root_cat.lower(), sub_cat.lower()],
                "is_featured": random.random() > 0.7,
                "is_best_seller": random.random() > 0.8,
                "status": "active",
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(10, 120)),
                "updated_at": datetime.now(timezone.utc),
            }
            res = await db.products.insert_one(doc)
            product_ids.append(res.inserted_id)
            await db.inventory.insert_one({
                "product_id": res.inserted_id,
                "warehouse_id": None,
                "quantity": doc["stock_quantity"],
                "reserved": 0,
                "min_level": doc["min_stock_level"],
                "updated_at": datetime.now(timezone.utc),
            })
    print(f"Products: {len(product_ids)}")

    # Customers
    customer_ids = []
    for i in range(80):
        div = random.choice(DIVISIONS)
        dist = random.choice(DISTRICTS[div])
        doc = {
            "full_name": f"Customer {i+1}",
            "email": f"customer{i+1}@example.bd",
            "phone": f"017{random.randint(10000000, 99999999)}",
            "password_hash": hash_password("Customer@123"),
            "status": "active",
            "addresses": [{
                "full_name": f"Customer {i+1}",
                "phone": f"017{random.randint(10000000, 99999999)}",
                "division": div,
                "district": dist,
                "upazila": dist,
                "address_line": f"House {random.randint(1,200)}, Road {random.randint(1,20)}",
                "postal_code": f"{random.randint(1000,9999)}",
            }],
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(5, 200)),
            "updated_at": datetime.now(timezone.utc),
        }
        r = await db.customers.insert_one(doc)
        customer_ids.append(r.inserted_id)
    print(f"Customers: {len(customer_ids)}")

    # Orders (last 90 days) â€“ enough for ML trends
    products = await db.products.find({"status": "active"}).to_list(100)
    order_count = 0
    for day_offset in range(90, 0, -1):
        day = datetime.now(timezone.utc) - timedelta(days=day_offset)
        n_orders = random.randint(3, 12)
        for _ in range(n_orders):
            cust = random.choice(customer_ids)
            n_items = random.randint(1, 4)
            chosen = random.sample(products, min(n_items, len(products)))
            items = []
            subtotal = 0.0
            for p in chosen:
                qty = random.randint(1, 3)
                unit = p["selling_price"] * (1 - p.get("discount_percent", 0) / 100)
                line = unit * qty
                subtotal += line
                items.append({
                    "product_id": p["_id"],
                    "name": p["name"],
                    "sku": p["sku"],
                    "quantity": qty,
                    "unit_price": round(unit, 2),
                    "line_total": round(line, 2),
                    "purchase_price": p.get("purchase_price", 0),
                })
            delivery = 60.0 if subtotal < 1000 else 0.0
            total = subtotal + delivery
            method = random.choices(
                [PaymentMethod.COD, PaymentMethod.BKASH, PaymentMethod.NAGAD],
                weights=[0.55, 0.3, 0.15],
            )[0]
            status = random.choices(
                [OrderStatus.DELIVERED, OrderStatus.SHIPPED, OrderStatus.PENDING, OrderStatus.CANCELLED],
                weights=[0.65, 0.15, 0.12, 0.08],
            )[0]
            pay_status = PaymentStatus.COD_COLLECTED if method == PaymentMethod.COD and status == OrderStatus.DELIVERED else (
                PaymentStatus.PAID if status == OrderStatus.DELIVERED else PaymentStatus.PENDING
            )
            div = random.choice(DIVISIONS)
            order = {
                "order_number": f"BD{day.strftime('%Y%m%d')}{random.randint(10000,99999)}",
                "customer_id": cust,
                "items": items,
                "subtotal": round(subtotal, 2),
                "discount": 0,
                "delivery_charge": delivery,
                "tax": 0,
                "total": round(total, 2),
                "currency": "BDT",
                "shipping_address": {
                    "full_name": "Demo",
                    "phone": "01700000000",
                    "division": div,
                    "district": random.choice(DISTRICTS[div]),
                    "upazila": "Sadar",
                    "address_line": "Demo address",
                },
                "payment_method": method,
                "payment_status": pay_status,
                "status": status,
                "created_at": day + timedelta(hours=random.randint(0, 23)),
                "updated_at": day,
                "history": [{"status": status, "at": day}],
            }
            await db.orders.insert_one(order)
            order_count += 1
    print(f"Orders: {order_count}")

    print("\nSeed complete.")
    print("Login (admin): admin@example.com / Admin@12345")
    print("Login (customer example): customer1@example.bd / Customer@123")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
