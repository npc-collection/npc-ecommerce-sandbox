"""E-commerce database models."""

from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class OrderStatus(str, Enum):
    """Order status enum."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Product(Base, TimestampMixin):
    """Product model."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    inventory: Mapped["Inventory"] = relationship(back_populates="product", uselist=False)
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="product")


class Inventory(Base, TimestampMixin):
    """Inventory model."""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=10)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=50)
    warehouse_location: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        """Get available quantity (total - reserved)."""
        return self.quantity - self.reserved_quantity


class Customer(Base, TimestampMixin):
    """Customer model."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Order(Base, TimestampMixin):
    """Order model."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.PENDING)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    shipping: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base, TimestampMixin):
    """Order item model."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class PriceHistory(Base, TimestampMixin):
    """Price history model for tracking price changes."""

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100))  # Agent or user who made the change

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="price_history")
