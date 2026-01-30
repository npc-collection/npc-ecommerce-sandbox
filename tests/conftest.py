"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator, Generator
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app modules
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///:memory:"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "test-key"

from api import app, create_app
from config import Settings, get_settings
from db.models.base import Base
from db.models.ecommerce import (
    Customer,
    Inventory,
    Product,
)


# Test settings
@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        app_env="test",
        debug=True,
        database_url="sqlite+aiosqlite:///:memory:",
        database_sync_url="sqlite:///:memory:",
        llm_provider="openai",
        openai_api_key="test-key",
    )


# Sync database engine for simple tests
@pytest.fixture
def sync_engine():
    """Create sync SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sync_session(sync_engine):
    """Create sync database session."""
    session_factory = sessionmaker(bind=sync_engine)
    session = session_factory()
    yield session
    session.close()


# Async database fixtures
@pytest.fixture
async def async_engine():
    """Create async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


# Sample data fixtures
@pytest.fixture
def sample_products() -> list[dict]:
    """Sample product data."""
    return [
        {
            "sku": "ELEC-001",
            "name": "Wireless Headphones",
            "description": "Premium wireless headphones with noise cancellation",
            "category": "electronics",
            "base_price": Decimal("149.99"),
            "current_price": Decimal("129.99"),
            "cost": Decimal("75.00"),
            "is_active": True,
        },
        {
            "sku": "ELEC-002",
            "name": "Smart Watch",
            "description": "Fitness tracking smart watch",
            "category": "electronics",
            "base_price": Decimal("299.99"),
            "current_price": Decimal("279.99"),
            "cost": Decimal("150.00"),
            "is_active": True,
        },
        {
            "sku": "CLOTH-001",
            "name": "Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt",
            "category": "clothing",
            "base_price": Decimal("29.99"),
            "current_price": Decimal("24.99"),
            "cost": Decimal("10.00"),
            "is_active": True,
        },
    ]


@pytest.fixture
def sample_customers() -> list[dict]:
    """Sample customer data."""
    return [
        {
            "email": "john.doe@example.com",
            "name": "John Doe",
            "phone": "+1-555-0101",
            "address": "123 Main St, Springfield, IL 62701",
            "loyalty_points": 500,
            "is_vip": False,
        },
        {
            "email": "jane.smith@example.com",
            "name": "Jane Smith",
            "phone": "+1-555-0102",
            "address": "456 Oak Ave, Chicago, IL 60601",
            "loyalty_points": 2500,
            "is_vip": True,
        },
    ]


@pytest.fixture
async def seeded_database(async_session, sample_products, sample_customers):
    """Seed database with test data."""
    # Create products
    products = []
    for data in sample_products:
        product = Product(**data)
        async_session.add(product)
        products.append(product)

    await async_session.flush()

    # Create inventory for each product
    for product in products:
        inventory = Inventory(
            product_id=product.id,
            quantity=100,
            reserved_quantity=0,
            reorder_point=10,
            reorder_quantity=50,
            warehouse_location="A1",
        )
        async_session.add(inventory)

    # Create customers
    customers = []
    for data in sample_customers:
        customer = Customer(**data)
        async_session.add(customer)
        customers.append(customer)

    await async_session.commit()

    return {"products": products, "customers": customers}


# FastAPI test client
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_app():
    """Create test application instance."""
    return create_app()


@pytest.fixture
def test_client(test_app) -> Generator[TestClient, None, None]:
    """Create test client with fresh app."""
    with TestClient(test_app) as client:
        yield client


# Mock LLM fixtures
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response from the AI assistant.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


@pytest.fixture
def mock_llm_client(mock_openai_response):
    """Create mock LLM client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(**mock_openai_response))
    return mock_client


@pytest.fixture
def mock_autogen_client():
    """Mock AutoGen model client."""
    mock = AsyncMock()
    mock.create = AsyncMock(
        return_value=MagicMock(
            content="Mock agent response",
            usage=MagicMock(prompt_tokens=10, completion_tokens=20),
        )
    )
    return mock


# Simulation fixtures
@pytest.fixture
def simulation_config():
    """Default simulation configuration."""
    return {
        "scenario": "normal_operations",
        "duration_minutes": 5,
        "order_rate_per_minute": 1.0,
        "include_price_changes": True,
        "include_inventory_events": True,
        "random_seed": 42,
    }


# Cleanup fixture
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Clear cached settings
    get_settings.cache_clear()
