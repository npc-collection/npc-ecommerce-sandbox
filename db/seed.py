"""Database initialization and seeding script."""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models.base import Base
from db.models.ecommerce import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
)

settings = get_settings()


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # Drop all tables (use with caution!)
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✓ Database tables created successfully")


async def seed_products(session: AsyncSession) -> list[Product]:
    """Seed initial products."""
    products_data = [
        {
            "sku": "LAPTOP-001",
            "name": 'Professional Laptop 15"',
            "description": "High-performance laptop for professionals",
            "category": "Electronics",
            "base_price": Decimal("1299.99"),
            "current_price": Decimal("1299.99"),
            "cost": Decimal("800.00"),
        },
        {
            "sku": "MOUSE-001",
            "name": "Wireless Gaming Mouse",
            "description": "Ergonomic wireless mouse with RGB lighting",
            "category": "Electronics",
            "base_price": Decimal("79.99"),
            "current_price": Decimal("79.99"),
            "cost": Decimal("35.00"),
        },
        {
            "sku": "KEYBOARD-001",
            "name": "Mechanical Keyboard",
            "description": "RGB mechanical keyboard with blue switches",
            "category": "Electronics",
            "base_price": Decimal("149.99"),
            "current_price": Decimal("149.99"),
            "cost": Decimal("70.00"),
        },
        {
            "sku": "MONITOR-001",
            "name": '4K Monitor 27"',
            "description": "Ultra HD 4K monitor with HDR support",
            "category": "Electronics",
            "base_price": Decimal("499.99"),
            "current_price": Decimal("499.99"),
            "cost": Decimal("280.00"),
        },
        {
            "sku": "HEADSET-001",
            "name": "Wireless Headset",
            "description": "Noise-cancelling wireless headset",
            "category": "Electronics",
            "base_price": Decimal("199.99"),
            "current_price": Decimal("199.99"),
            "cost": Decimal("90.00"),
        },
        {
            "sku": "DESK-001",
            "name": "Standing Desk",
            "description": "Adjustable height standing desk",
            "category": "Furniture",
            "base_price": Decimal("599.99"),
            "current_price": Decimal("599.99"),
            "cost": Decimal("300.00"),
        },
        {
            "sku": "CHAIR-001",
            "name": "Ergonomic Office Chair",
            "description": "Premium ergonomic chair with lumbar support",
            "category": "Furniture",
            "base_price": Decimal("399.99"),
            "current_price": Decimal("399.99"),
            "cost": Decimal("180.00"),
        },
        {
            "sku": "WEBCAM-001",
            "name": "4K Webcam",
            "description": "Professional 4K webcam with auto-focus",
            "category": "Electronics",
            "base_price": Decimal("129.99"),
            "current_price": Decimal("129.99"),
            "cost": Decimal("55.00"),
        },
        {
            "sku": "SPEAKER-001",
            "name": "Bluetooth Speaker",
            "description": "Portable Bluetooth speaker with 360° sound",
            "category": "Electronics",
            "base_price": Decimal("89.99"),
            "current_price": Decimal("89.99"),
            "cost": Decimal("40.00"),
        },
        {
            "sku": "TABLET-001",
            "name": 'Tablet 10"',
            "description": "Lightweight tablet with stylus support",
            "category": "Electronics",
            "base_price": Decimal("449.99"),
            "current_price": Decimal("449.99"),
            "cost": Decimal("250.00"),
        },
    ]

    products = []
    for data in products_data:
        product = Product(**data)
        session.add(product)
        products.append(product)

    await session.flush()
    print(f"✓ Created {len(products)} products")
    return products


async def seed_inventory(session: AsyncSession, products: list[Product]):
    """Seed initial inventory."""
    inventory_data = [
        {"product_id": products[0].id, "quantity": 50, "reorder_point": 10, "reorder_quantity": 30},
        {
            "product_id": products[1].id,
            "quantity": 150,
            "reorder_point": 20,
            "reorder_quantity": 100,
        },
        {"product_id": products[2].id, "quantity": 80, "reorder_point": 15, "reorder_quantity": 50},
        {"product_id": products[3].id, "quantity": 40, "reorder_point": 8, "reorder_quantity": 25},
        {
            "product_id": products[4].id,
            "quantity": 100,
            "reorder_point": 20,
            "reorder_quantity": 60,
        },
        {"product_id": products[5].id, "quantity": 25, "reorder_point": 5, "reorder_quantity": 15},
        {"product_id": products[6].id, "quantity": 35, "reorder_point": 8, "reorder_quantity": 20},
        {
            "product_id": products[7].id,
            "quantity": 120,
            "reorder_point": 25,
            "reorder_quantity": 75,
        },
        {"product_id": products[8].id, "quantity": 90, "reorder_point": 18, "reorder_quantity": 55},
        {"product_id": products[9].id, "quantity": 60, "reorder_point": 12, "reorder_quantity": 40},
    ]

    for data in inventory_data:
        inventory = Inventory(**data)
        session.add(inventory)

    await session.flush()
    print(f"✓ Created inventory for {len(inventory_data)} products")


async def seed_customers(session: AsyncSession) -> list[Customer]:
    """Seed initial customers."""
    customers_data = [
        {
            "email": "john.doe@example.com",
            "name": "John Doe",
            "phone": "+1-555-0101",
            "address": "123 Main St, New York, NY 10001",
            "loyalty_points": 500,
            "is_vip": True,
        },
        {
            "email": "jane.smith@example.com",
            "name": "Jane Smith",
            "phone": "+1-555-0102",
            "address": "456 Oak Ave, Los Angeles, CA 90001",
            "loyalty_points": 250,
            "is_vip": False,
        },
        {
            "email": "bob.johnson@example.com",
            "name": "Bob Johnson",
            "phone": "+1-555-0103",
            "address": "789 Pine Rd, Chicago, IL 60601",
            "loyalty_points": 1200,
            "is_vip": True,
        },
        {
            "email": "alice.williams@example.com",
            "name": "Alice Williams",
            "phone": "+1-555-0104",
            "address": "321 Elm St, Houston, TX 77001",
            "loyalty_points": 100,
            "is_vip": False,
        },
        {
            "email": "charlie.brown@example.com",
            "name": "Charlie Brown",
            "phone": "+1-555-0105",
            "address": "654 Maple Dr, Phoenix, AZ 85001",
            "loyalty_points": 750,
            "is_vip": True,
        },
    ]

    customers = []
    for data in customers_data:
        customer = Customer(**data)
        session.add(customer)
        customers.append(customer)

    await session.flush()
    print(f"✓ Created {len(customers)} customers")
    return customers


async def seed_sample_orders(
    session: AsyncSession, customers: list[Customer], products: list[Product]
):
    """Seed sample orders."""
    # Order 1: John Doe orders laptop and mouse
    order1 = Order(
        order_number="ORD-2024-001",
        customer_id=customers[0].id,
        status=OrderStatus.DELIVERED,
        subtotal=Decimal("1379.98"),
        tax=Decimal("110.40"),
        shipping=Decimal("0.00"),
        total=Decimal("1490.38"),
        shipping_address=customers[0].address,
    )
    session.add(order1)
    await session.flush()

    session.add(
        OrderItem(
            order_id=order1.id,
            product_id=products[0].id,
            quantity=1,
            unit_price=products[0].current_price,
            total_price=products[0].current_price,
        )
    )
    session.add(
        OrderItem(
            order_id=order1.id,
            product_id=products[1].id,
            quantity=1,
            unit_price=products[1].current_price,
            total_price=products[1].current_price,
        )
    )

    # Order 2: Jane Smith orders keyboard and headset
    order2 = Order(
        order_number="ORD-2024-002",
        customer_id=customers[1].id,
        status=OrderStatus.SHIPPED,
        subtotal=Decimal("349.98"),
        tax=Decimal("28.00"),
        shipping=Decimal("15.00"),
        total=Decimal("392.98"),
        shipping_address=customers[1].address,
    )
    session.add(order2)
    await session.flush()

    session.add(
        OrderItem(
            order_id=order2.id,
            product_id=products[2].id,
            quantity=1,
            unit_price=products[2].current_price,
            total_price=products[2].current_price,
        )
    )
    session.add(
        OrderItem(
            order_id=order2.id,
            product_id=products[4].id,
            quantity=1,
            unit_price=products[4].current_price,
            total_price=products[4].current_price,
        )
    )

    # Order 3: Bob Johnson orders standing desk
    order3 = Order(
        order_number="ORD-2024-003",
        customer_id=customers[2].id,
        status=OrderStatus.PROCESSING,
        subtotal=Decimal("599.99"),
        tax=Decimal("48.00"),
        shipping=Decimal("0.00"),
        total=Decimal("647.99"),
        shipping_address=customers[2].address,
    )
    session.add(order3)
    await session.flush()

    session.add(
        OrderItem(
            order_id=order3.id,
            product_id=products[5].id,
            quantity=1,
            unit_price=products[5].current_price,
            total_price=products[5].current_price,
        )
    )

    print("✓ Created 3 sample orders")


async def seed_database():
    """Seed the database with initial data."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # Check if data already exists
            result = await session.execute(select(Product))
            existing_products = result.scalars().all()

            if existing_products:
                print("⚠ Database already contains data. Skipping seed.")
                return

            print("Seeding database...")

            # Seed data
            products = await seed_products(session)
            await seed_inventory(session, products)
            customers = await seed_customers(session)
            await seed_sample_orders(session, customers, products)

            print("✓ Database seeded successfully")

    await engine.dispose()


async def reset_database():
    """Reset the database (drop and recreate all tables)."""
    print("⚠ WARNING: This will delete all data!")

    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ Dropped all tables")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Created all tables")

    await engine.dispose()


async def main():
    """Main function."""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "create":
            await create_tables()
        elif command == "seed":
            await seed_database()
        elif command == "reset":
            await reset_database()
            await seed_database()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m npc_ecommerce_sandbox.db.init [create|seed|reset]")
    else:
        # Default: create tables and seed
        await create_tables()
        await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
