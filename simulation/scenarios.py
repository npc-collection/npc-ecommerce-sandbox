"""Pre-defined simulation scenarios for testing agent behaviors."""

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ScenarioType(str, Enum):
    """Available simulation scenarios."""

    NORMAL_OPERATIONS = "normal_operations"
    FLASH_SALE = "flash_sale"
    SUPPLY_SHORTAGE = "supply_shortage"
    SEASONAL_PEAK = "seasonal_peak"
    COMPETITOR_PRICE_WAR = "competitor_price_war"
    NEW_PRODUCT_LAUNCH = "new_product_launch"
    DEMAND_SPIKE = "demand_spike"
    SLOW_PERIOD = "slow_period"


@dataclass
class ScenarioConfig:
    """Configuration for a simulation scenario."""

    name: str
    description: str
    order_rate_multiplier: float  # Multiplier for base order rate
    price_volatility: float  # 0.0-1.0, higher = more price changes
    inventory_pressure: float  # 0.0-1.0, higher = more inventory depletion
    customer_support_load: float  # 0.0-1.0, higher = more support tickets
    duration_minutes: int  # Suggested duration
    special_behaviors: dict  # Scenario-specific parameters


# Pre-defined scenarios
SCENARIOS: dict[ScenarioType, ScenarioConfig] = {
    ScenarioType.NORMAL_OPERATIONS: ScenarioConfig(
        name="Normal Operations",
        description="Standard day-to-day e-commerce operations with steady order flow",
        order_rate_multiplier=1.0,
        price_volatility=0.1,
        inventory_pressure=0.3,
        customer_support_load=0.2,
        duration_minutes=60,
        special_behaviors={},
    ),
    ScenarioType.FLASH_SALE: ScenarioConfig(
        name="Flash Sale",
        description="24-hour flash sale with heavy discounts causing order surge",
        order_rate_multiplier=5.0,
        price_volatility=0.05,  # Prices locked during sale
        inventory_pressure=0.8,  # High inventory depletion
        customer_support_load=0.6,  # More questions about deals
        duration_minutes=30,
        special_behaviors={
            "discount_percent": 30,
            "featured_categories": ["electronics", "clothing"],
            "stock_depletion_rate": 2.0,
        },
    ),
    ScenarioType.SUPPLY_SHORTAGE: ScenarioConfig(
        name="Supply Shortage",
        description="Supply chain disruption causing low stock and delayed restocking",
        order_rate_multiplier=0.8,
        price_volatility=0.4,  # Prices may increase due to scarcity
        inventory_pressure=0.9,  # Very high depletion, slow replenishment
        customer_support_load=0.7,  # Many out-of-stock inquiries
        duration_minutes=120,
        special_behaviors={
            "restock_delay_multiplier": 3.0,
            "affected_categories": ["electronics"],
            "price_increase_threshold": 0.15,
        },
    ),
    ScenarioType.SEASONAL_PEAK: ScenarioConfig(
        name="Seasonal Peak",
        description="Holiday shopping season with sustained high demand",
        order_rate_multiplier=3.0,
        price_volatility=0.2,
        inventory_pressure=0.6,
        customer_support_load=0.5,
        duration_minutes=180,
        special_behaviors={
            "gift_wrapping_rate": 0.4,
            "express_shipping_rate": 0.3,
            "bundle_purchase_rate": 0.25,
        },
    ),
    ScenarioType.COMPETITOR_PRICE_WAR: ScenarioConfig(
        name="Competitor Price War",
        description="Aggressive pricing competition requiring dynamic price adjustments",
        order_rate_multiplier=1.5,
        price_volatility=0.8,  # Very high price changes
        inventory_pressure=0.4,
        customer_support_load=0.3,
        duration_minutes=90,
        special_behaviors={
            "competitor_price_range": (-0.15, 0.05),  # Competitors 15% lower to 5% higher
            "price_match_enabled": True,
            "margin_floor": 0.05,  # Minimum 5% margin
        },
    ),
    ScenarioType.NEW_PRODUCT_LAUNCH: ScenarioConfig(
        name="New Product Launch",
        description="Launch of new products with marketing push and initial demand",
        order_rate_multiplier=2.0,
        price_volatility=0.15,
        inventory_pressure=0.5,
        customer_support_load=0.6,  # Many product questions
        duration_minutes=60,
        special_behaviors={
            "new_product_skus": ["NEW-001", "NEW-002"],
            "launch_discount": 0.10,
            "review_request_rate": 0.5,
        },
    ),
    ScenarioType.DEMAND_SPIKE: ScenarioConfig(
        name="Demand Spike",
        description="Sudden viral demand for specific products (social media trend)",
        order_rate_multiplier=8.0,
        price_volatility=0.3,
        inventory_pressure=0.95,  # Extreme depletion
        customer_support_load=0.4,
        duration_minutes=20,
        special_behaviors={
            "viral_products": ["SKU-001"],
            "backorder_enabled": True,
            "waitlist_enabled": True,
        },
    ),
    ScenarioType.SLOW_PERIOD: ScenarioConfig(
        name="Slow Period",
        description="Low-traffic period for testing efficiency and cost optimization",
        order_rate_multiplier=0.3,
        price_volatility=0.2,  # May run promotions
        inventory_pressure=0.1,
        customer_support_load=0.1,
        duration_minutes=120,
        special_behaviors={
            "promotion_trigger_threshold": 0.5,  # Trigger promos if too slow
            "staff_optimization": True,
        },
    ),
}


def get_scenario(scenario_type: ScenarioType | str) -> ScenarioConfig:
    """Get scenario configuration by type.

    Args:
        scenario_type: The scenario type (string or enum)

    Returns:
        ScenarioConfig for the requested scenario

    Raises:
        ValueError: If scenario type is not found
    """
    if isinstance(scenario_type, str):
        scenario_type = ScenarioType(scenario_type)

    if scenario_type not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_type}")

    return SCENARIOS[scenario_type]


def list_scenarios() -> list[dict]:
    """List all available scenarios with their descriptions.

    Returns:
        List of scenario info dictionaries
    """
    return [
        {
            "type": scenario_type.value,
            "name": config.name,
            "description": config.description,
            "duration_minutes": config.duration_minutes,
            "order_rate_multiplier": config.order_rate_multiplier,
        }
        for scenario_type, config in SCENARIOS.items()
    ]
