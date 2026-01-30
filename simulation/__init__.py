"""Simulation module for e-commerce events."""

from .engine import (
    SimulationEngine,
    generate_random_order,
    get_simulation_engine,
    trigger_low_stock_event,
    trigger_price_change_event,
)
from .scenarios import (
    SCENARIOS,
    ScenarioConfig,
    ScenarioType,
    get_scenario,
    list_scenarios,
)

__all__ = [
    # Engine
    "SimulationEngine",
    "get_simulation_engine",
    "generate_random_order",
    "trigger_low_stock_event",
    "trigger_price_change_event",
    # Scenarios
    "ScenarioType",
    "ScenarioConfig",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
