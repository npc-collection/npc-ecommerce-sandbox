"""Tests for simulation scenarios."""

import pytest

from npc_ecommerce_sandbox.simulation.scenarios import (
    ScenarioType,
    ScenarioConfig,
    SCENARIOS,
    get_scenario,
    list_scenarios,
)


class TestScenarioType:
    """Tests for ScenarioType enum."""

    def test_scenario_type_values(self):
        """Test scenario type enum values."""
        assert ScenarioType.NORMAL_OPERATIONS.value == "normal_operations"
        assert ScenarioType.FLASH_SALE.value == "flash_sale"
        assert ScenarioType.SUPPLY_SHORTAGE.value == "supply_shortage"
        assert ScenarioType.SEASONAL_PEAK.value == "seasonal_peak"
        assert ScenarioType.COMPETITOR_PRICE_WAR.value == "competitor_price_war"
        assert ScenarioType.NEW_PRODUCT_LAUNCH.value == "new_product_launch"
        assert ScenarioType.DEMAND_SPIKE.value == "demand_spike"
        assert ScenarioType.SLOW_PERIOD.value == "slow_period"

    def test_scenario_type_from_string(self):
        """Test creating scenario type from string."""
        assert ScenarioType("normal_operations") == ScenarioType.NORMAL_OPERATIONS
        assert ScenarioType("flash_sale") == ScenarioType.FLASH_SALE

    def test_invalid_scenario_type(self):
        """Test invalid scenario type raises error."""
        with pytest.raises(ValueError):
            ScenarioType("invalid_scenario")


class TestScenarioConfig:
    """Tests for ScenarioConfig dataclass."""

    def test_scenario_config_creation(self):
        """Test creating a scenario config."""
        config = ScenarioConfig(
            name="Test Scenario",
            description="A test scenario",
            order_rate_multiplier=2.0,
            price_volatility=0.5,
            inventory_pressure=0.6,
            customer_support_load=0.3,
            duration_minutes=30,
            special_behaviors={"test_key": "test_value"},
        )

        assert config.name == "Test Scenario"
        assert config.order_rate_multiplier == 2.0
        assert config.price_volatility == 0.5
        assert config.special_behaviors["test_key"] == "test_value"


class TestSCENARIOS:
    """Tests for SCENARIOS dictionary."""

    def test_all_scenario_types_defined(self):
        """Test all scenario types have configurations."""
        for scenario_type in ScenarioType:
            assert scenario_type in SCENARIOS, f"Missing config for {scenario_type}"

    def test_normal_operations_scenario(self):
        """Test normal operations scenario configuration."""
        scenario = SCENARIOS[ScenarioType.NORMAL_OPERATIONS]

        assert scenario.name == "Normal Operations"
        assert scenario.order_rate_multiplier == 1.0
        assert 0 <= scenario.price_volatility <= 1
        assert 0 <= scenario.inventory_pressure <= 1
        assert scenario.duration_minutes > 0

    def test_flash_sale_scenario(self):
        """Test flash sale scenario configuration."""
        scenario = SCENARIOS[ScenarioType.FLASH_SALE]

        assert scenario.name == "Flash Sale"
        assert scenario.order_rate_multiplier > 1.0  # Higher than normal
        assert "discount_percent" in scenario.special_behaviors
        assert scenario.special_behaviors["discount_percent"] > 0

    def test_supply_shortage_scenario(self):
        """Test supply shortage scenario configuration."""
        scenario = SCENARIOS[ScenarioType.SUPPLY_SHORTAGE]

        assert scenario.name == "Supply Shortage"
        assert scenario.inventory_pressure > 0.5  # High pressure
        assert "restock_delay_multiplier" in scenario.special_behaviors

    def test_competitor_price_war_scenario(self):
        """Test competitor price war scenario configuration."""
        scenario = SCENARIOS[ScenarioType.COMPETITOR_PRICE_WAR]

        assert scenario.name == "Competitor Price War"
        assert scenario.price_volatility > 0.5  # High volatility
        assert "competitor_price_range" in scenario.special_behaviors
        assert "price_match_enabled" in scenario.special_behaviors

    def test_demand_spike_scenario(self):
        """Test demand spike scenario configuration."""
        scenario = SCENARIOS[ScenarioType.DEMAND_SPIKE]

        assert scenario.name == "Demand Spike"
        assert scenario.order_rate_multiplier >= 5.0  # Very high
        assert scenario.inventory_pressure > 0.8  # Extreme pressure


class TestGetScenario:
    """Tests for get_scenario function."""

    def test_get_scenario_by_enum(self):
        """Test getting scenario by enum type."""
        scenario = get_scenario(ScenarioType.FLASH_SALE)

        assert isinstance(scenario, ScenarioConfig)
        assert scenario.name == "Flash Sale"

    def test_get_scenario_by_string(self):
        """Test getting scenario by string."""
        scenario = get_scenario("flash_sale")

        assert isinstance(scenario, ScenarioConfig)
        assert scenario.name == "Flash Sale"

    def test_get_scenario_invalid_type(self):
        """Test getting invalid scenario raises error."""
        with pytest.raises(ValueError):
            get_scenario("invalid_scenario")

    def test_get_all_scenarios(self):
        """Test getting all scenarios works."""
        for scenario_type in ScenarioType:
            scenario = get_scenario(scenario_type)
            assert isinstance(scenario, ScenarioConfig)
            assert scenario.name is not None
            assert scenario.description is not None


class TestListScenarios:
    """Tests for list_scenarios function."""

    def test_list_scenarios_returns_list(self):
        """Test list_scenarios returns a list."""
        scenarios = list_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) == len(ScenarioType)

    def test_list_scenarios_format(self):
        """Test list_scenarios returns correct format."""
        scenarios = list_scenarios()

        for scenario in scenarios:
            assert "type" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "duration_minutes" in scenario
            assert "order_rate_multiplier" in scenario

    def test_list_scenarios_types(self):
        """Test list_scenarios includes all scenario types."""
        scenarios = list_scenarios()
        types = [s["type"] for s in scenarios]

        for scenario_type in ScenarioType:
            assert scenario_type.value in types


class TestScenarioValidation:
    """Tests for scenario configuration validation."""

    def test_all_scenarios_have_valid_multipliers(self):
        """Test all scenarios have valid multipliers."""
        for scenario_type, config in SCENARIOS.items():
            assert config.order_rate_multiplier > 0, f"{scenario_type} has invalid order rate"
            assert 0 <= config.price_volatility <= 1, f"{scenario_type} has invalid volatility"
            assert 0 <= config.inventory_pressure <= 1, f"{scenario_type} has invalid pressure"
            assert 0 <= config.customer_support_load <= 1, f"{scenario_type} has invalid support load"

    def test_all_scenarios_have_positive_duration(self):
        """Test all scenarios have positive duration."""
        for scenario_type, config in SCENARIOS.items():
            assert config.duration_minutes > 0, f"{scenario_type} has invalid duration"

    def test_all_scenarios_have_descriptions(self):
        """Test all scenarios have non-empty descriptions."""
        for scenario_type, config in SCENARIOS.items():
            assert config.name, f"{scenario_type} has no name"
            assert config.description, f"{scenario_type} has no description"
            assert len(config.description) > 10, f"{scenario_type} has too short description"
