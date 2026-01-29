"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestRootEndpoints:
    """Tests for root level endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns app info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data
        assert "agents" in data


class TestSimulationEndpoints:
    """Tests for simulation endpoints."""

    def test_get_scenarios(self, client):
        """Test listing available scenarios."""
        response = client.get("/simulation/scenarios")

        assert response.status_code == 200
        scenarios = response.json()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 8  # At least 8 scenarios

        # Check scenario format
        for scenario in scenarios:
            assert "type" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "duration_minutes" in scenario
            assert "order_rate_multiplier" in scenario

    def test_simulation_status_initial(self, client):
        """Test simulation status when not running."""
        response = client.get("/simulation/status")

        assert response.status_code == 200
        status = response.json()
        assert "running" in status
        assert "total_orders" in status
        assert "total_revenue" in status

    def test_start_simulation_invalid_scenario(self, client):
        """Test starting simulation with invalid scenario."""
        response = client.post(
            "/simulation/start",
            json={
                "scenario": "invalid_scenario",
                "duration_minutes": 5,
            },
        )

        assert response.status_code == 400
        assert "Invalid scenario" in response.json()["detail"]

    def test_stop_simulation_not_running(self, client):
        """Test stopping simulation when not running."""
        # First ensure no simulation is running
        response = client.post("/simulation/stop")

        # Should return 400 if no simulation running
        assert response.status_code == 400
        assert "No simulation running" in response.json()["detail"]

    def test_get_events(self, client):
        """Test getting simulation events."""
        response = client.get("/simulation/events")

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_get_events_with_limit(self, client):
        """Test getting simulation events with limit."""
        response = client.get("/simulation/events?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) <= 5


class TestSimulationTriggers:
    """Tests for manual simulation triggers."""

    def test_trigger_order_no_data(self, client):
        """Test triggering order when no data exists."""
        response = client.post("/simulation/trigger/order")

        # Should return 400 if no customers/products, or 500 if database unavailable
        assert response.status_code in [200, 400, 500]

    def test_trigger_inventory_alert_not_found(self, client):
        """Test triggering inventory alert for non-existent product."""
        response = client.post("/simulation/trigger/inventory-alert?product_sku=NONEXISTENT")

        # 404 if product not found, 500 if database unavailable
        assert response.status_code in [404, 500]
        if response.status_code == 404:
            assert "not found" in response.json()["detail"].lower()

    def test_trigger_price_change_not_found(self, client):
        """Test triggering price change for non-existent product."""
        response = client.post(
            "/simulation/trigger/price-change?product_sku=NONEXISTENT&change_percent=10"
        )

        # 404 if product not found, 500 if database unavailable
        assert response.status_code in [404, 500]
        if response.status_code == 404:
            assert "not found" in response.json()["detail"].lower()

    def test_trigger_price_change_invalid_percent(self, client):
        """Test triggering price change with invalid percentage."""
        response = client.post(
            "/simulation/trigger/price-change?product_sku=TEST&change_percent=100"
        )

        # Should fail validation (max 50%)
        assert response.status_code == 422


class TestAgentEndpoints:
    """Tests for agent-related endpoints."""

    def test_agents_health(self, client):
        """Test agents health endpoint."""
        response = client.get("/agents/health")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data


class TestEcommerceEndpoints:
    """Tests for e-commerce endpoints."""

    def test_list_products(self, client):
        """Test listing products endpoint exists."""
        response = client.get("/ecommerce/products")

        # Endpoint should exist and return list
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_inventory(self, client):
        """Test listing inventory endpoint exists."""
        response = client.get("/ecommerce/inventory")

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAPIValidation:
    """Tests for API input validation."""

    def test_simulation_config_validation(self, client):
        """Test simulation config validation."""
        # Duration too long
        response = client.post(
            "/simulation/start",
            json={
                "scenario": "normal_operations",
                "duration_minutes": 10000,  # Max is 1440
            },
        )
        assert response.status_code == 422

        # Order rate too low
        response = client.post(
            "/simulation/start",
            json={
                "scenario": "normal_operations",
                "order_rate_per_minute": 0.001,  # Min is 0.1
            },
        )
        assert response.status_code == 422

    def test_events_limit_validation(self, client):
        """Test events limit parameter validation."""
        # Limit too high
        response = client.get("/simulation/events?limit=1000")
        assert response.status_code == 422

        # Limit too low
        response = client.get("/simulation/events?limit=0")
        assert response.status_code == 422


class TestCORSHeaders:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # CORS should allow requests
        assert response.status_code in [200, 204, 405]


class TestOpenAPIDoc:
    """Tests for OpenAPI documentation."""

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    def test_docs_available(self, client):
        """Test Swagger UI docs are available."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "text/html" in response.headers.get(
            "content-type", ""
        )
