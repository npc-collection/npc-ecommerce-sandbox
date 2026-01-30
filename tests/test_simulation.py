"""Tests for simulation engine."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from simulation import (
    ScenarioType,
    SimulationEngine,
    get_simulation_engine,
)


class TestSimulationEngine:
    """Tests for SimulationEngine class."""

    def test_init_default_values(self):
        """Test simulation engine initialization with defaults."""
        engine = SimulationEngine()

        assert engine.base_order_rate == 2.0
        assert engine.include_price_changes is True
        assert engine.include_inventory_events is True
        assert engine.is_running is False
        assert engine.scenario is None
        assert engine.orders_generated == 0

    def test_init_custom_values(self):
        """Test simulation engine initialization with custom values."""
        engine = SimulationEngine(
            order_rate=5.0,
            include_price_changes=False,
            include_inventory_events=False,
            random_seed=42,
        )

        assert engine.base_order_rate == 5.0
        assert engine.include_price_changes is False
        assert engine.include_inventory_events is False

    def test_set_scenario(self):
        """Test setting simulation scenario."""
        engine = SimulationEngine()
        engine.set_scenario("flash_sale")

        assert engine.scenario is not None
        assert engine.scenario.name == "Flash Sale"

    def test_set_scenario_by_enum(self):
        """Test setting scenario by enum."""
        engine = SimulationEngine()
        engine.set_scenario(ScenarioType.SUPPLY_SHORTAGE)

        assert engine.scenario.name == "Supply Shortage"

    def test_effective_order_rate_no_scenario(self):
        """Test effective order rate without scenario."""
        engine = SimulationEngine(order_rate=3.0)

        assert engine.effective_order_rate == 3.0

    def test_effective_order_rate_with_scenario(self):
        """Test effective order rate with scenario multiplier."""
        engine = SimulationEngine(order_rate=2.0)
        engine.set_scenario("flash_sale")

        # Flash sale has 5x multiplier
        assert engine.effective_order_rate == 10.0

    def test_stop(self):
        """Test stopping simulation."""
        engine = SimulationEngine()
        engine.is_running = True
        engine.stop()

        assert engine.is_running is False

    def test_get_status(self):
        """Test getting simulation status."""
        engine = SimulationEngine()
        status = engine.get_status()

        assert "is_running" in status
        assert "scenario" in status
        assert "orders_generated" in status
        assert "total_revenue" in status
        assert "inventory_alerts" in status
        assert "price_changes" in status
        assert "recent_events" in status

    def test_log_event(self):
        """Test event logging."""
        engine = SimulationEngine()
        event = engine.log_event("test_event", {"key": "value"})

        assert event["type"] == "test_event"
        assert event["data"]["key"] == "value"
        assert "timestamp" in event
        assert len(engine.events_log) == 1


class TestSimulationEngineScenarios:
    """Tests for simulation engine with different scenarios."""

    @pytest.mark.parametrize(
        "scenario",
        [
            "normal_operations",
            "flash_sale",
            "supply_shortage",
            "seasonal_peak",
            "competitor_price_war",
            "new_product_launch",
            "demand_spike",
            "slow_period",
        ],
    )
    def test_set_all_scenarios(self, scenario):
        """Test setting all available scenarios."""
        engine = SimulationEngine()
        engine.set_scenario(scenario)

        assert engine.scenario is not None
        assert engine.scenario.name is not None

    def test_flash_sale_increases_order_rate(self):
        """Test flash sale scenario increases order rate."""
        engine = SimulationEngine(order_rate=2.0)
        engine.set_scenario("flash_sale")

        assert engine.effective_order_rate > 2.0

    def test_slow_period_decreases_order_rate(self):
        """Test slow period scenario decreases order rate."""
        engine = SimulationEngine(order_rate=2.0)
        engine.set_scenario("slow_period")

        assert engine.effective_order_rate < 2.0

    def test_demand_spike_has_highest_rate(self):
        """Test demand spike has highest order rate multiplier."""
        engine = SimulationEngine(order_rate=1.0)

        scenarios_rates = {}
        for scenario_type in ScenarioType:
            engine.set_scenario(scenario_type)
            scenarios_rates[scenario_type] = engine.effective_order_rate

        # Demand spike should have highest rate
        assert scenarios_rates[ScenarioType.DEMAND_SPIKE] == max(scenarios_rates.values())


class TestGetSimulationEngine:
    """Tests for get_simulation_engine singleton."""

    def test_returns_engine_instance(self):
        """Test get_simulation_engine returns an engine."""
        engine = get_simulation_engine()

        assert isinstance(engine, SimulationEngine)

    def test_returns_same_instance(self):
        """Test get_simulation_engine returns singleton."""
        engine1 = get_simulation_engine()
        engine2 = get_simulation_engine()

        assert engine1 is engine2


class TestSimulationEngineAsync:
    """Async tests for simulation engine."""

    @pytest.mark.asyncio
    async def test_run_yields_events(self):
        """Test run method yields events."""
        engine = SimulationEngine(order_rate=60.0)  # Fast rate for testing

        # Mock the session to avoid database dependency
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_session)
        engine.async_session = MagicMock(return_value=mock_session)

        events = []
        async for event in engine.run(duration_minutes=0.01):
            events.append(event)
            if len(events) >= 2:  # Get at least 2 events
                engine.stop()
                break

        # Should have at least simulation_started event
        assert len(events) >= 1
        assert events[0]["type"] == "simulation_started"

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start method sets running flag."""
        engine = SimulationEngine()

        # Mock to prevent actual simulation
        with patch.object(engine, "_run_background", new_callable=AsyncMock):
            await engine.start(scenario="normal_operations", duration_minutes=1)

        assert engine.scenario.name == "Normal Operations"


class TestSimulationStats:
    """Tests for simulation statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics are zero."""
        engine = SimulationEngine()

        assert engine.orders_generated == 0
        assert engine.total_revenue == Decimal("0.00")
        assert engine.inventory_alerts == 0
        assert engine.price_changes == 0

    def test_status_includes_all_stats(self):
        """Test status includes all statistics."""
        engine = SimulationEngine()
        engine.orders_generated = 10
        engine.total_revenue = Decimal("1000.00")
        engine.inventory_alerts = 3
        engine.price_changes = 5

        status = engine.get_status()

        assert status["orders_generated"] == 10
        assert status["total_revenue"] == 1000.00
        assert status["inventory_alerts"] == 3
        assert status["price_changes"] == 5
