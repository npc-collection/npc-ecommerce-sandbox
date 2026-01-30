"""Simulation engine for generating e-commerce events."""

import asyncio
import logging
import random
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import get_settings
from db.models.ecommerce import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    PriceHistory,
    Product,
)

from .scenarios import ScenarioConfig, ScenarioType, get_scenario

logger = logging.getLogger(__name__)

settings = get_settings()


class SimulationEngine:
    """E-commerce simulation engine with scenario support."""

    def __init__(
        self,
        order_rate: float = 2.0,
        include_price_changes: bool = True,
        include_inventory_events: bool = True,
        random_seed: int | None = None,
    ):
        """Initialize the simulation engine.

        Args:
            order_rate: Base orders per minute
            include_price_changes: Whether to simulate price changes
            include_inventory_events: Whether to simulate inventory events
            random_seed: Optional seed for reproducible simulations
        """
        self.base_order_rate = order_rate
        self.include_price_changes = include_price_changes
        self.include_inventory_events = include_inventory_events
        self.rng = random.Random(random_seed)

        self.is_running = False
        self.scenario: ScenarioConfig | None = None
        self.start_time: datetime | None = None
        self.orders_generated = 0
        self.total_revenue = Decimal("0.00")
        self.inventory_alerts = 0
        self.price_changes = 0
        self.events_log: list[dict] = []

        # Create async session
        engine = create_async_engine(settings.database_url, echo=False)
        self.async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    def set_scenario(self, scenario_type: ScenarioType | str) -> None:
        """Set the simulation scenario.

        Args:
            scenario_type: The scenario to use
        """
        self.scenario = get_scenario(scenario_type)
        self.log_event("scenario_set", {"scenario": self.scenario.name})

    @property
    def effective_order_rate(self) -> float:
        """Get the effective order rate based on scenario."""
        multiplier = self.scenario.order_rate_multiplier if self.scenario else 1.0
        return self.base_order_rate * multiplier

    async def run(
        self,
        duration_minutes: int = 60,
        scenario: ScenarioType | str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Run the simulation and yield events.

        Args:
            duration_minutes: How long to run the simulation
            scenario: Optional scenario to apply

        Yields:
            Event dictionaries as they occur
        """
        if scenario:
            self.set_scenario(scenario)

        self.is_running = True
        self.start_time = datetime.now()
        self.orders_generated = 0
        self.total_revenue = Decimal("0.00")
        self.inventory_alerts = 0
        self.price_changes = 0
        self.events_log = []

        yield self.log_event(
            "simulation_started",
            {
                "scenario": self.scenario.name if self.scenario else "default",
                "duration_minutes": duration_minutes,
                "order_rate": self.effective_order_rate,
            },
        )

        end_time = self.start_time + timedelta(minutes=duration_minutes)

        while self.is_running and datetime.now() < end_time:
            try:
                elapsed = (datetime.now() - self.start_time).total_seconds() / 60

                # Generate order
                order_event = await self._generate_order()
                if order_event:
                    order_event["elapsed_minutes"] = elapsed
                    yield order_event

                # Trigger inventory events based on scenario
                if self.include_inventory_events:
                    inv_probability = (
                        self.scenario.inventory_pressure if self.scenario else 0.3
                    ) * 0.2
                    if self.rng.random() < inv_probability:
                        inv_event = await self._trigger_inventory_event()
                        if inv_event:
                            inv_event["elapsed_minutes"] = elapsed
                            yield inv_event

                # Trigger price changes based on scenario
                if self.include_price_changes:
                    price_probability = (
                        self.scenario.price_volatility if self.scenario else 0.1
                    ) * 0.1
                    if self.rng.random() < price_probability:
                        price_event = await self._trigger_price_change()
                        if price_event:
                            price_event["elapsed_minutes"] = elapsed
                            yield price_event

                # Wait based on order rate
                wait_seconds = 60 / self.effective_order_rate
                # Add some randomness to timing
                wait_seconds *= self.rng.uniform(0.5, 1.5)
                await asyncio.sleep(wait_seconds)

            except Exception as e:
                yield self.log_event("simulation_error", {"error": str(e)})

        self.is_running = False
        yield self.log_event(
            "simulation_completed",
            {
                "total_orders": self.orders_generated,
                "total_revenue": float(self.total_revenue),
                "inventory_alerts": self.inventory_alerts,
                "price_changes": self.price_changes,
                "duration": str(datetime.now() - self.start_time),
            },
        )

    async def start(
        self,
        scenario: str = "normal_operations",
        duration_minutes: int = 60,
        order_rate: int = 10,
    ) -> None:
        """Start the simulation (legacy method for backward compatibility)."""
        self.base_order_rate = order_rate
        self.set_scenario(scenario)

        # Run simulation in background
        asyncio.create_task(self._run_background(duration_minutes))

    async def _run_background(self, duration_minutes: int) -> None:
        """Run simulation in background (legacy support)."""
        async for event in self.run(duration_minutes):
            pass  # Events are logged internally

    def stop(self) -> None:
        """Stop the simulation."""
        self.is_running = False
        self.log_event(
            "simulation_stopped",
            {
                "orders_generated": self.orders_generated,
                "duration": str(datetime.now() - self.start_time) if self.start_time else "0",
            },
        )

    def get_status(self) -> dict:
        """Get simulation status."""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0

        return {
            "is_running": self.is_running,
            "scenario": self.scenario.name if self.scenario else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_minutes": round(elapsed, 2),
            "order_rate": self.effective_order_rate,
            "orders_generated": self.orders_generated,
            "total_revenue": float(self.total_revenue),
            "inventory_alerts": self.inventory_alerts,
            "price_changes": self.price_changes,
            "recent_events": self.events_log[-10:],
        }

    def log_event(self, event_type: str, data: dict) -> dict:
        """Log a simulation event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.events_log.append(event)
        logger.info("%s: %s", event_type, data)
        return event

    async def _generate_order(self) -> dict | None:
        """Generate a random order based on scenario."""
        async with self.async_session() as session:
            async with session.begin():
                # Get random customer
                result = await session.execute(select(Customer))
                customers = result.scalars().all()
                if not customers:
                    return None

                customer = self.rng.choice(customers)

                # Get products based on scenario
                query = select(Product).where(Product.is_active)
                result = await session.execute(query)
                products = result.scalars().all()
                if not products:
                    return None

                # Apply scenario-specific product selection
                if self.scenario and "featured_categories" in self.scenario.special_behaviors:
                    featured = self.scenario.special_behaviors["featured_categories"]
                    featured_products = [p for p in products if p.category in featured]
                    if featured_products and self.rng.random() < 0.7:
                        products = featured_products

                # Select 1-5 products (more during peak scenarios)
                max_items = 5 if self.scenario and self.scenario.order_rate_multiplier > 2 else 3
                num_items = self.rng.randint(1, min(max_items, len(products)))
                selected_products = self.rng.sample(products, num_items)

                # Calculate totals
                subtotal = Decimal("0.00")
                items_data = []

                for product in selected_products:
                    # Quantity based on scenario
                    if self.scenario and self.scenario.order_rate_multiplier > 3:
                        quantity = self.rng.randint(1, 5)  # Larger orders during peaks
                    else:
                        quantity = self.rng.randint(1, 3)

                    # Apply scenario discounts
                    price = product.current_price
                    if self.scenario and "discount_percent" in self.scenario.special_behaviors:
                        discount = Decimal(
                            str(self.scenario.special_behaviors["discount_percent"] / 100)
                        )
                        price = price * (Decimal("1.00") - discount)
                        price = price.quantize(Decimal("0.01"))

                    item_total = price * quantity
                    subtotal += item_total

                    items_data.append(
                        {
                            "product_id": product.id,
                            "product_name": product.name,
                            "quantity": quantity,
                            "unit_price": price,
                            "total_price": item_total,
                        }
                    )

                tax = subtotal * Decimal("0.08")
                shipping = Decimal("15.00") if subtotal < Decimal("100.00") else Decimal("0.00")
                total = subtotal + tax + shipping

                # Create order
                order_number = (
                    f"ORD-{datetime.now().strftime('%Y%m%d')}-{self.orders_generated + 1:04d}"
                )

                order = Order(
                    order_number=order_number,
                    customer_id=customer.id,
                    status=OrderStatus.PENDING,
                    subtotal=subtotal,
                    tax=tax,
                    shipping=shipping,
                    total=total,
                    shipping_address=customer.address,
                )
                session.add(order)
                await session.flush()

                # Create order items
                for item_data in items_data:
                    item = OrderItem(
                        order_id=order.id,
                        product_id=item_data["product_id"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        total_price=item_data["total_price"],
                    )
                    session.add(item)

                self.orders_generated += 1
                self.total_revenue += total

                return self.log_event(
                    "order",
                    {
                        "order_number": order_number,
                        "customer": customer.name,
                        "customer_email": customer.email,
                        "items": len(items_data),
                        "subtotal": float(subtotal),
                        "total": float(total),
                        "amount": float(total),  # For API compatibility
                    },
                )

    async def _trigger_inventory_event(self) -> dict | None:
        """Trigger an inventory event based on scenario."""
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(select(Inventory).join(Product))
                inventories = result.scalars().all()
                if not inventories:
                    return None

                inventory = self.rng.choice(inventories)

                # Depletion vs replenishment based on scenario
                depletion_chance = self.scenario.inventory_pressure if self.scenario else 0.5

                if self.rng.random() < depletion_chance:
                    # Deplete inventory
                    base_depletion = self.rng.randint(5, 20)
                    if self.scenario and "stock_depletion_rate" in self.scenario.special_behaviors:
                        base_depletion = int(
                            base_depletion * self.scenario.special_behaviors["stock_depletion_rate"]
                        )

                    old_quantity = inventory.quantity
                    inventory.quantity = max(0, inventory.quantity - base_depletion)

                    event_data = {
                        "product_id": inventory.product_id,
                        "old_quantity": old_quantity,
                        "new_quantity": inventory.quantity,
                        "change": -base_depletion,
                    }

                    # Check for low stock alert
                    if inventory.quantity <= inventory.reorder_point:
                        self.inventory_alerts += 1
                        event_data["alert"] = "low_stock"
                        event_data["reorder_point"] = inventory.reorder_point
                        return self.log_event("inventory_alert", event_data)

                    return self.log_event("inventory_depleted", event_data)
                else:
                    # Replenish inventory
                    replenishment = inventory.reorder_quantity

                    # Delay replenishment during supply shortage
                    if (
                        self.scenario
                        and "restock_delay_multiplier" in self.scenario.special_behaviors
                    ):
                        if self.rng.random() < 0.7:  # 70% chance of delayed restock
                            return self.log_event(
                                "restock_delayed",
                                {
                                    "product_id": inventory.product_id,
                                    "reason": "supply_chain_disruption",
                                },
                            )

                    old_quantity = inventory.quantity
                    inventory.quantity += replenishment

                    return self.log_event(
                        "inventory_replenished",
                        {
                            "product_id": inventory.product_id,
                            "old_quantity": old_quantity,
                            "new_quantity": inventory.quantity,
                            "change": replenishment,
                        },
                    )

    async def _trigger_price_change(self) -> dict | None:
        """Trigger a price change based on scenario."""
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(select(Product).where(Product.is_active))
                products = result.scalars().all()
                if not products:
                    return None

                product = self.rng.choice(products)
                old_price = product.current_price

                # Calculate price change based on scenario
                if self.scenario and "competitor_price_range" in self.scenario.special_behaviors:
                    # Price war scenario - respond to competitor prices
                    low, high = self.scenario.special_behaviors["competitor_price_range"]
                    competitor_change = Decimal(str(self.rng.uniform(low, high)))

                    # Match or beat competitor
                    if self.scenario.special_behaviors.get("price_match_enabled"):
                        adjustment = competitor_change - Decimal("0.01")
                    else:
                        adjustment = Decimal(str(self.rng.uniform(-0.05, 0.05)))

                    # Enforce margin floor
                    margin_floor = self.scenario.special_behaviors.get("margin_floor", 0.05)
                    min_price = product.cost * Decimal(str(1 + margin_floor))
                elif self.scenario and self.scenario.price_volatility < 0.1:
                    # Low volatility (e.g., during flash sale) - minimal changes
                    return None
                else:
                    # Normal price adjustment
                    volatility = self.scenario.price_volatility if self.scenario else 0.1
                    adjustment = Decimal(str(self.rng.uniform(-volatility, volatility)))
                    min_price = product.cost * Decimal("1.05")

                new_price = product.current_price * (Decimal("1.00") + adjustment)
                new_price = max(new_price, min_price)  # Don't go below cost + margin
                new_price = new_price.quantize(Decimal("0.01"))

                if new_price == old_price:
                    return None

                product.current_price = new_price

                # Record price history
                history = PriceHistory(
                    product_id=product.id,
                    old_price=old_price,
                    new_price=new_price,
                    reason=(
                        "Simulation: "
                        f"{self.scenario.name if self.scenario else 'dynamic_adjustment'}"
                    ),
                    changed_by="simulation_engine",
                )
                session.add(history)

                self.price_changes += 1

                return self.log_event(
                    "price_change",
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "product_sku": product.sku,
                        "old_price": float(old_price),
                        "new_price": float(new_price),
                        "change_percent": float((new_price - old_price) / old_price * 100),
                    },
                )


# Global simulation instance
_simulation_engine: SimulationEngine | None = None


def get_simulation_engine() -> SimulationEngine:
    """Get the global simulation engine instance."""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = SimulationEngine()
    return _simulation_engine


# Convenience functions for API routes


async def generate_random_order() -> dict:
    """Generate a single random order.

    Returns:
        Order data dictionary
    """
    engine = get_simulation_engine()
    event = await engine._generate_order()
    if event:
        return event["data"]
    return {"error": "Could not generate order - no customers or products in database"}


async def trigger_low_stock_event(product_sku: str) -> dict:
    """Trigger a low stock event for a specific product.

    Args:
        product_sku: The product SKU to deplete

    Returns:
        Event data dictionary
    """
    engine = get_simulation_engine()

    async with engine.async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Inventory).join(Product).where(Product.sku == product_sku)
            )
            inventory = result.scalar_one_or_none()

            if not inventory:
                return {"error": f"Product {product_sku} not found"}

            old_quantity = inventory.quantity
            # Set to below reorder point
            inventory.quantity = max(0, inventory.reorder_point - 5)

            engine.inventory_alerts += 1

            return {
                "product_sku": product_sku,
                "old_quantity": old_quantity,
                "new_quantity": inventory.quantity,
                "reorder_point": inventory.reorder_point,
                "alert": "low_stock_triggered",
            }


async def trigger_price_change_event(product_sku: str, change_percent: float) -> dict:
    """Trigger a price change for a specific product.

    Args:
        product_sku: The product SKU to change
        change_percent: Percentage change (-100 to 100)

    Returns:
        Event data dictionary
    """
    engine = get_simulation_engine()

    async with engine.async_session() as session:
        async with session.begin():
            result = await session.execute(select(Product).where(Product.sku == product_sku))
            product = result.scalar_one_or_none()

            if not product:
                return {"error": f"Product {product_sku} not found"}

            old_price = product.current_price
            adjustment = Decimal(str(change_percent / 100))
            new_price = product.current_price * (Decimal("1.00") + adjustment)

            # Ensure we don't go below cost
            min_price = product.cost * Decimal("1.05")
            new_price = max(new_price, min_price)
            new_price = new_price.quantize(Decimal("0.01"))

            product.current_price = new_price

            # Record price history
            history = PriceHistory(
                product_id=product.id,
                old_price=old_price,
                new_price=new_price,
                reason=f"Manual trigger: {change_percent}% change",
                changed_by="api_trigger",
            )
            session.add(history)

            engine.price_changes += 1

            return {
                "product_sku": product_sku,
                "product_name": product.name,
                "old_price": float(old_price),
                "new_price": float(new_price),
                "change_percent": float(change_percent),
            }
