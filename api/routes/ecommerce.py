"""API routes for e-commerce data."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ecommerce", tags=["ecommerce"])


# Pydantic models for API
class ProductBase(BaseModel):
    """Base product model."""

    sku: str
    name: str
    description: str | None = None
    category: str
    base_price: Decimal
    current_price: Decimal
    cost: Decimal


class ProductCreate(ProductBase):
    """Model for creating a product."""

    pass


class ProductResponse(ProductBase):
    """Response model for product."""

    id: int
    is_active: bool

    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    """Response model for inventory."""

    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_point: int
    reorder_quantity: int
    warehouse_location: str | None = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Response model for order."""

    id: int
    order_number: str
    customer_id: int
    status: str
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics model."""

    total_products: int
    total_orders: int
    total_revenue: Decimal
    low_stock_items: int
    pending_orders: int
    active_customers: int


# Mock data for initial development (replace with database queries)
MOCK_PRODUCTS = [
    {
        "id": 1,
        "sku": "LAPTOP-001",
        "name": "Pro Laptop 15",
        "description": "High-performance laptop",
        "category": "Electronics",
        "base_price": Decimal("999.99"),
        "current_price": Decimal("899.99"),
        "cost": Decimal("600.00"),
        "is_active": True,
    },
    {
        "id": 2,
        "sku": "PHONE-001",
        "name": "SmartPhone X",
        "description": "Latest smartphone",
        "category": "Electronics",
        "base_price": Decimal("699.99"),
        "current_price": Decimal("649.99"),
        "cost": Decimal("400.00"),
        "is_active": True,
    },
    {
        "id": 3,
        "sku": "HEADPHONES-001",
        "name": "Wireless Headphones",
        "description": "Noise-canceling headphones",
        "category": "Audio",
        "base_price": Decimal("199.99"),
        "current_price": Decimal("179.99"),
        "cost": Decimal("80.00"),
        "is_active": True,
    },
]


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List all products with optional filtering."""
    products = MOCK_PRODUCTS
    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    return products[skip : skip + limit]


@router.get("/products/{sku}", response_model=ProductResponse)
async def get_product(sku: str):
    """Get a single product by SKU."""
    for product in MOCK_PRODUCTS:
        if product["sku"] == sku:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@router.get("/inventory", response_model=list[InventoryResponse])
async def list_inventory(low_stock_only: bool = False):
    """List inventory for all products."""
    mock_inventory = [
        {
            "id": 1,
            "product_id": 1,
            "quantity": 50,
            "reserved_quantity": 5,
            "available_quantity": 45,
            "reorder_point": 20,
            "reorder_quantity": 50,
            "warehouse_location": "A-1-1",
        },
        {
            "id": 2,
            "product_id": 2,
            "quantity": 100,
            "reserved_quantity": 10,
            "available_quantity": 90,
            "reorder_point": 30,
            "reorder_quantity": 100,
            "warehouse_location": "A-1-2",
        },
        {
            "id": 3,
            "product_id": 3,
            "quantity": 15,
            "reserved_quantity": 3,
            "available_quantity": 12,
            "reorder_point": 25,
            "reorder_quantity": 75,
            "warehouse_location": "B-2-1",
        },
    ]

    if low_stock_only:
        mock_inventory = [
            i for i in mock_inventory if i["available_quantity"] <= i["reorder_point"]
        ]

    return mock_inventory


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """List orders with optional status filter."""
    mock_orders = [
        {
            "id": 1,
            "order_number": "ORD-00000001",
            "customer_id": 1,
            "status": "processing",
            "subtotal": Decimal("899.99"),
            "tax": Decimal("72.00"),
            "shipping": Decimal("0.00"),
            "total": Decimal("971.99"),
        },
        {
            "id": 2,
            "order_number": "ORD-00000002",
            "customer_id": 2,
            "status": "pending",
            "subtotal": Decimal("179.99"),
            "tax": Decimal("14.40"),
            "shipping": Decimal("5.99"),
            "total": Decimal("200.38"),
        },
    ]

    if status:
        mock_orders = [o for o in mock_orders if o["status"] == status.lower()]

    return mock_orders[skip : skip + limit]


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    return DashboardStats(
        total_products=len(MOCK_PRODUCTS),
        total_orders=156,
        total_revenue=Decimal("45678.90"),
        low_stock_items=3,
        pending_orders=12,
        active_customers=89,
    )
