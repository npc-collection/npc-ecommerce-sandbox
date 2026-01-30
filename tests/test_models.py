"""Tests for database models."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.base import Base
from db.models.ecommerce import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    PriceHistory,
    Product,
)


@pytest.fixture
def db_session():
    """Create in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    yield session
    session.close()


class TestProductModel:
    """Tests for Product model."""

    def test_create_product(self, db_session):
        """Test creating a product."""
        product = Product(
            sku="TEST-001",
            name="Test Product",
            description="A test product",
            category="test",
            base_price=Decimal("99.99"),
            current_price=Decimal("89.99"),
            cost=Decimal("50.00"),
            is_active=True,
        )
        db_session.add(product)
        db_session.commit()

        assert product.id is not None
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.base_price == Decimal("99.99")
        assert product.current_price == Decimal("89.99")

    def test_product_unique_sku(self, db_session):
        """Test that SKU must be unique."""
        product1 = Product(
            sku="UNIQUE-001",
            name="Product 1",
            category="test",
            base_price=Decimal("10.00"),
            current_price=Decimal("10.00"),
            cost=Decimal("5.00"),
        )
        db_session.add(product1)
        db_session.commit()

        product2 = Product(
            sku="UNIQUE-001",  # Same SKU
            name="Product 2",
            category="test",
            base_price=Decimal("20.00"),
            current_price=Decimal("20.00"),
            cost=Decimal("10.00"),
        )
        db_session.add(product2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_product_default_active(self, db_session):
        """Test product is active by default."""
        product = Product(
            sku="DEFAULT-001",
            name="Default Product",
            category="test",
            base_price=Decimal("10.00"),
            current_price=Decimal("10.00"),
            cost=Decimal("5.00"),
        )
        db_session.add(product)
        db_session.commit()

        assert product.is_active is True


class TestInventoryModel:
    """Tests for Inventory model."""

    def test_create_inventory(self, db_session):
        """Test creating inventory for a product."""
        product = Product(
            sku="INV-001",
            name="Inventory Product",
            category="test",
            base_price=Decimal("50.00"),
            current_price=Decimal("50.00"),
            cost=Decimal("25.00"),
        )
        db_session.add(product)
        db_session.flush()

        inventory = Inventory(
            product_id=product.id,
            quantity=100,
            reserved_quantity=10,
            reorder_point=20,
            reorder_quantity=50,
            warehouse_location="A1-B2",
        )
        db_session.add(inventory)
        db_session.commit()

        assert inventory.id is not None
        assert inventory.quantity == 100
        assert inventory.reserved_quantity == 10

    def test_available_quantity_property(self, db_session):
        """Test available_quantity calculated property."""
        product = Product(
            sku="AVAIL-001",
            name="Available Product",
            category="test",
            base_price=Decimal("30.00"),
            current_price=Decimal("30.00"),
            cost=Decimal("15.00"),
        )
        db_session.add(product)
        db_session.flush()

        inventory = Inventory(
            product_id=product.id,
            quantity=100,
            reserved_quantity=25,
            reorder_point=10,
            reorder_quantity=50,
        )
        db_session.add(inventory)
        db_session.commit()

        assert inventory.available_quantity == 75  # 100 - 25


class TestCustomerModel:
    """Tests for Customer model."""

    def test_create_customer(self, db_session):
        """Test creating a customer."""
        customer = Customer(
            email="test@example.com",
            name="Test Customer",
            phone="+1-555-0100",
            address="123 Test St",
            loyalty_points=100,
            is_vip=False,
        )
        db_session.add(customer)
        db_session.commit()

        assert customer.id is not None
        assert customer.email == "test@example.com"
        assert customer.loyalty_points == 100

    def test_customer_unique_email(self, db_session):
        """Test that email must be unique."""
        customer1 = Customer(
            email="unique@example.com",
            name="Customer 1",
        )
        db_session.add(customer1)
        db_session.commit()

        customer2 = Customer(
            email="unique@example.com",  # Same email
            name="Customer 2",
        )
        db_session.add(customer2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_customer_default_values(self, db_session):
        """Test customer default values."""
        customer = Customer(
            email="defaults@example.com",
            name="Default Customer",
        )
        db_session.add(customer)
        db_session.commit()

        assert customer.loyalty_points == 0
        assert customer.is_vip is False


class TestOrderModel:
    """Tests for Order model."""

    def test_create_order(self, db_session):
        """Test creating an order."""
        customer = Customer(email="order@example.com", name="Order Customer")
        db_session.add(customer)
        db_session.flush()

        order = Order(
            order_number="ORD-TEST-001",
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("100.00"),
            tax=Decimal("8.00"),
            shipping=Decimal("10.00"),
            total=Decimal("118.00"),
            shipping_address="123 Order St",
        )
        db_session.add(order)
        db_session.commit()

        assert order.id is not None
        assert order.order_number == "ORD-TEST-001"
        assert order.status == OrderStatus.PENDING
        assert order.total == Decimal("118.00")

    def test_order_status_values(self):
        """Test order status enum values."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.CONFIRMED.value == "confirmed"
        assert OrderStatus.PROCESSING.value == "processing"
        assert OrderStatus.SHIPPED.value == "shipped"
        assert OrderStatus.DELIVERED.value == "delivered"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.REFUNDED.value == "refunded"

    def test_order_customer_relationship(self, db_session):
        """Test order-customer relationship."""
        customer = Customer(email="rel@example.com", name="Related Customer")
        db_session.add(customer)
        db_session.flush()

        order = Order(
            order_number="ORD-REL-001",
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("50.00"),
            tax=Decimal("4.00"),
            shipping=Decimal("5.00"),
            total=Decimal("59.00"),
        )
        db_session.add(order)
        db_session.commit()

        # Refresh to get relationships
        db_session.refresh(order)
        assert order.customer.email == "rel@example.com"


class TestOrderItemModel:
    """Tests for OrderItem model."""

    def test_create_order_item(self, db_session):
        """Test creating an order item."""
        # Create product
        product = Product(
            sku="ITEM-001",
            name="Item Product",
            category="test",
            base_price=Decimal("25.00"),
            current_price=Decimal("25.00"),
            cost=Decimal("12.00"),
        )
        db_session.add(product)

        # Create customer and order
        customer = Customer(email="item@example.com", name="Item Customer")
        db_session.add(customer)
        db_session.flush()

        order = Order(
            order_number="ORD-ITEM-001",
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("75.00"),
            tax=Decimal("6.00"),
            shipping=Decimal("0.00"),
            total=Decimal("81.00"),
        )
        db_session.add(order)
        db_session.flush()

        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=3,
            unit_price=Decimal("25.00"),
            total_price=Decimal("75.00"),
        )
        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.quantity == 3
        assert item.total_price == Decimal("75.00")


class TestPriceHistoryModel:
    """Tests for PriceHistory model."""

    def test_create_price_history(self, db_session):
        """Test creating price history entry."""
        product = Product(
            sku="HIST-001",
            name="History Product",
            category="test",
            base_price=Decimal("100.00"),
            current_price=Decimal("90.00"),
            cost=Decimal("50.00"),
        )
        db_session.add(product)
        db_session.flush()

        history = PriceHistory(
            product_id=product.id,
            old_price=Decimal("100.00"),
            new_price=Decimal("90.00"),
            reason="Promotional discount",
            changed_by="pricing_agent",
        )
        db_session.add(history)
        db_session.commit()

        assert history.id is not None
        assert history.old_price == Decimal("100.00")
        assert history.new_price == Decimal("90.00")
        assert history.changed_by == "pricing_agent"
