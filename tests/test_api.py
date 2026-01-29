"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from npc_ecommerce_sandbox.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NPC-Ecommerce-Sandbox"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_products(client):
    """Test listing products."""
    response = client.get("/ecommerce/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0


def test_list_inventory(client):
    """Test listing inventory."""
    response = client.get("/ecommerce/inventory")
    assert response.status_code == 200
    inventory = response.json()
    assert isinstance(inventory, list)


def test_dashboard_stats(client):
    """Test dashboard statistics."""
    response = client.get("/ecommerce/dashboard/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_products" in stats
    assert "total_orders" in stats
    assert "total_revenue" in stats


def test_agents_health(client):
    """Test agents health endpoint."""
    response = client.get("/agents/health")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "crewai" in data["agents"]
    assert "autogen" in data["agents"]


def test_simulation_status(client):
    """Test simulation status endpoint."""
    response = client.get("/simulation/status")
    assert response.status_code == 200
    status = response.json()
    assert "running" in status
    assert "total_orders" in status
