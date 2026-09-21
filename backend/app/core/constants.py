from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"


class AdminRole(str, Enum):
    MAIN_ADMIN = "main_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_MANAGER = "sales_manager"
    INVENTORY_MANAGER = "inventory_manager"
    ACCOUNTANT = "accountant"
    PURCHASE_MANAGER = "purchase_manager"
    CUSTOMER_SUPPORT = "customer_support"
    WAREHOUSE_STAFF = "warehouse_staff"
    DELIVERY_MANAGER = "delivery_manager"
    MARKETING_MANAGER = "marketing_manager"
    ANALYST = "analyst"
    NETWORK_ADMIN = "network_admin"


# Granular permissions (module.action)
PERMISSIONS = [
    # Products
    "products.view", "products.create", "products.edit", "products.delete",
    # Categories
    "categories.view", "categories.create", "categories.edit", "categories.delete",
    # Orders
    "orders.view", "orders.edit", "orders.cancel", "orders.refund",
    # Inventory
    "inventory.view", "inventory.add", "inventory.edit", "inventory.transfer",
    # Users / Customers
    "users.view", "users.edit", "users.disable",
    # Administrators
    "admins.view", "admins.create", "admins.edit", "admins.disable", "admins.delete", "admins.assign_roles",
    # Promotions
    "promotions.view", "promotions.create", "promotions.edit", "promotions.pause", "promotions.cancel",
    # Finance
    "finance.view", "finance.create", "finance.edit", "finance.export",
    # ML
    "ml.view_predictions", "ml.run_analysis", "ml.train_model", "ml.retrain_model",
    # Network
    "network.view", "network.manage", "network.view_logs",
    # Reports
    "reports.view", "reports.export",
    # Settings
    "settings.view", "settings.edit",
    # Audit
    "audit.view",
]

# Default role → permissions mapping
ROLE_PERMISSIONS: dict[str, list[str]] = {
    AdminRole.MAIN_ADMIN: PERMISSIONS,  # all
    AdminRole.ADMIN: [
        "products.view", "products.create", "products.edit", "products.delete",
        "categories.view", "categories.create", "categories.edit", "categories.delete",
        "orders.view", "orders.edit", "orders.cancel", "orders.refund",
        "inventory.view", "inventory.add", "inventory.edit",
        "users.view", "users.edit",
        "promotions.view", "promotions.create", "promotions.edit",
        "finance.view", "finance.create",
        "ml.view_predictions", "ml.run_analysis",
        "reports.view", "reports.export",
        "audit.view",
    ],
    AdminRole.MANAGER: [
        "products.view", "products.edit",
        "orders.view", "orders.edit",
        "inventory.view",
        "users.view",
        "reports.view",
        "ml.view_predictions",
    ],
    AdminRole.SALES_MANAGER: [
        "products.view",
        "orders.view", "orders.edit", "orders.cancel",
        "users.view",
        "reports.view",
        "ml.view_predictions",
    ],
    AdminRole.INVENTORY_MANAGER: [
        "products.view", "products.edit",
        "inventory.view", "inventory.add", "inventory.edit", "inventory.transfer",
        "categories.view",
        "ml.view_predictions",
        "reports.view",
    ],
    AdminRole.ACCOUNTANT: [
        "orders.view",
        "finance.view", "finance.create", "finance.edit", "finance.export",
        "reports.view", "reports.export",
    ],
    AdminRole.PURCHASE_MANAGER: [
        "inventory.view", "inventory.add",
        "products.view",
        "reports.view",
    ],
    AdminRole.CUSTOMER_SUPPORT: [
        "orders.view", "orders.edit",
        "users.view", "users.edit",
    ],
    AdminRole.WAREHOUSE_STAFF: [
        "inventory.view", "inventory.add", "inventory.edit",
        "orders.view",
    ],
    AdminRole.DELIVERY_MANAGER: [
        "orders.view", "orders.edit",
    ],
    AdminRole.MARKETING_MANAGER: [
        "products.view",
        "promotions.view", "promotions.create", "promotions.edit", "promotions.pause",
        "ml.view_predictions",
    ],
    AdminRole.ANALYST: [
        "products.view",
        "orders.view",
        "ml.view_predictions", "ml.run_analysis",
        "reports.view", "reports.export",
        "finance.view",
    ],
    AdminRole.NETWORK_ADMIN: [
        "network.view", "network.manage", "network.view_logs",
        "audit.view",
        "settings.view",
    ],
}


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    COD_PENDING = "cod_pending"
    COD_COLLECTED = "cod_collected"


class PaymentMethod(str, Enum):
    COD = "cod"
    BKASH = "bkash"
    NAGAD = "nagad"
    ROCKET = "rocket"
    CARD = "card"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


# Bangladesh divisions (for localization)
BD_DIVISIONS = [
    "Dhaka", "Chattogram", "Rajshahi", "Khulna",
    "Barishal", "Sylhet", "Rangpur", "Mymensingh",
]