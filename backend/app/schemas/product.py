from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    sku: str
    color: Optional[str] = None
    size: Optional[str] = None
    stock: int = 0
    price: float
    purchase_price: Optional[float] = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    category_id: str
    brand: Optional[str] = None
    purchase_price: float
    selling_price: float
    discount_percent: float = 0
    tax_percent: float = 0
    stock_quantity: int = 0
    min_stock_level: int = 5
    supplier_id: Optional[str] = None
    images: List[str] = []
    videos: List[str] = []
    variants: List[ProductVariant] = []
    tags: List[str] = []
    is_featured: bool = False
    is_best_seller: bool = False
    status: str = "active"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    discount_percent: Optional[float] = None
    tax_percent: Optional[float] = None
    stock_quantity: Optional[int] = None
    min_stock_level: Optional[int] = None
    supplier_id: Optional[str] = None
    images: Optional[List[str]] = None
    variants: Optional[List[ProductVariant]] = None
    tags: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    is_best_seller: Optional[bool] = None
    status: Optional[str] = None


class ProductOut(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    barcode: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    category_id: str
    brand: Optional[str] = None
    purchase_price: float
    selling_price: float
    discount_percent: float
    tax_percent: float
    final_price: float
    stock_quantity: int
    min_stock_level: int
    available_stock: int
    stock_status: str
    supplier_id: Optional[str] = None
    images: List[str]
    variants: List[Any]
    tags: List[str]
    is_featured: bool
    is_best_seller: bool
    status: str
    intelligence_score: Optional[float] = None
    demand_trend: Optional[str] = None
    predicted_demand_30d: Optional[float] = None
    created_at: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    order: int = 0
    status: str = "active"


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    order: int
    status: str
    children: List[Any] = []