"""Tests for simulation engine."""

import pytest
from npc_ecommerce_sandbox.simulation import SimulationEngine, generate_random_order


@pytest.mark.asyncio
async def test_generate_random_order():
    """Test generating a random order."""
    order = await generate_random_order()

    assert "order_number" in order
    assert order["order_number"].startswith("ORD-")
    assert "customer" in order
    assert "items" in order
    assert len(order["items"]) > 0
    assert "amount" in order
    assert order["amount"] > 0


@pytest.mark.asyncio
async def test_simulation_engine_init():
    """Test simulation engine initialization."""
    engine = SimulationEngine(
        order_rate=5.0,
        include_price_changes=True,
        include_inventory_events=True,
        random_seed=42,
    )

    assert engine.order_rate == 5.0
    assert engine.include_price_changes is True
    assert engine.include_inventory_events is True
    assert len(engine.products) > 0
    assert len(engine.customers) > 0


def test_simulation_engine_products():
    """Test simulation engine has products."""
    engine = SimulationEngine()

    assert len(engine.products) == 8
    for product in engine.products:
        assert "sku" in product
        assert "name" in product
        assert "price" in product
        assert "stock" in product
