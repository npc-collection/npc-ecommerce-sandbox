"""Simulation engine for generating e-commerce events."""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from npc_ecommerce_sandbox.config import get_settings
from npc_ecommerce_sandbox.db.models.ecommerce import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
)

settings = get_settings()


class SimulationEngine:
    """E-commerce simulation engine."""

    def __init__(self):
        """Initialize the simulation engine."""
        self.is_running = False
        self.scenario = "normal_operations"
        self.order_rate = 10  # orders per minute
        self.duration_minutes = 60
        self.start_time: Optional[datetime] = None
        self.orders_generated = 0
        self.events_log: List[Dict] = []

        # Create async session
        engine = create_async_engine(settings.database_url, echo=False)
        self.async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def start(
        self, scenario: str = "normal_operations", duration_minutes: int = 60, order_rate: int = 10
    ):
        """Start the simulation."""
        self.scenario = scenario
        self.duration_minutes = duration_minutes
        self.order_rate = order_rate
        self.is_running = True
        self.start_time = datetime.now()
        self.orders_generated = 0
        self.events_log = []

        self.log_event(
            "simulation_started",
            {
                "scenario": scenario,
                "duration_minutes": duration_minutes,
                "order_rate": order_rate,
            },
        )

        # Run simulation in background
        asyncio.create_task(self._run_simulation())

    def stop(self):
        """Stop the simulation."""
        self.is_running = False
        self.log_event(
            "simulation_stopped",
            {
                "orders_generated": self.orders_generated,
                "duration": str(datetime.now() - self.start_time) if self.start_time else "0",
            },
        )

    def get_status(self) -> Dict:
        """Get simulation status."""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0

        return {
            "is_running": self.is_running,
            "scenario": self.scenario,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_minutes": round(elapsed, 2),
            "duration_minutes": self.duration_minutes,
            "order_rate": self.order_rate,
            "orders_generated": self.orders_generated,
            "recent_events": self.events_log[-10:],  # Last 10 events
        }

    def log_event(self, event_type: str, data: Dict):
        """Log a simulation event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.events_log.append(event)
        print(f"[SIMULATION] {event_type}: {data}")

    async def _run_simulation(self):
        """Run the simulation loop."""
        end_time = self.start_time + timedelta(minutes=self.duration_minutes)

        while self.is_running and datetime.now() < end_time:
            try:
                # Generate order based on scenario
                await self._generate_order()

                # Randomly trigger other events
                if random.random() < 0.1:  # 10% chance
                    await self._trigger_inventory_event()

                if random.random() < 0.05:  # 5% chance
                    await self._trigger_price_change()

                # Wait based on order rate
                wait_seconds = 60 / self.order_rate
                await asyncio.sleep(wait_seconds)

            except Exception as e:
                self.log_event("simulation_error", {"error": str(e)})

        self.is_running = False
        self.log_event(
            "simulation_completed",
            {
                "total_orders": self.orders_generated,
                "duration": str(datetime.now() - self.start_time),
            },
        )

    async def _generate_order(self):
        """Generate a random order."""
        async with self.async_session() as session:
            async with session.begin():
                # Get random customer
                result = await session.execute(select(Customer))
                customers = result.scalars().all()
                if not customers:
                    return

                customer = random.choice(customers)

                # Get random products
                result = await session.execute(select(Product).where(Product.is_active == True))
                products = result.scalars().all()
                if not products:
                    return

                # Select 1-3 random products
                num_items = random.randint(1, min(3, len(products)))
                selected_products = random.sample(products, num_items)

                # Calculate totals
                subtotal = Decimal("0.00")
                items_data = []

                for product in selected_products:
                    quantity = random.randint(1, 3)
                    item_total = product.current_price * quantity
                    subtotal += item_total

                    items_data.append(
                        {
                            "product_id": product.id,
                            "quantity": quantity,
                            "unit_price": product.current_price,
                            "total_price": item_total,
                        }
                    )

                tax = subtotal * Decimal("0.08")  # 8% tax
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
                    item = OrderItem(order_id=order.id, **item_data)
                    session.add(item)

                self.orders_generated += 1

                self.log_event(
                    "order_generated",
                    {
                        "order_number": order_number,
                        "customer": customer.name,
                        "items": len(items_data),
                        "total": float(total),
                    },
                )

    async def _trigger_inventory_event(self):
        """Trigger a random inventory event."""
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(select(Inventory))
                inventories = result.scalars().all()
                if not inventories:
                    return

                inventory = random.choice(inventories)

                # Randomly deplete or replenish
                if random.random() < 0.7:  # 70% chance to deplete
                    depletion = random.randint(5, 20)
                    inventory.quantity = max(0, inventory.quantity - depletion)

                    self.log_event(
                        "inventory_depleted",
                        {
                            "product_id": inventory.product_id,
                            "amount": depletion,
                            "new_quantity": inventory.quantity,
                        },
                    )
                else:  # 30% chance to replenish
                    replenishment = random.randint(20, 50)
                    inventory.quantity += replenishment

                    self.log_event(
                        "inventory_replenished",
                        {
                            "product_id": inventory.product_id,
                            "amount": replenishment,
                            "new_quantity": inventory.quantity,
                        },
                    )

    async def _trigger_price_change(self):
        """Trigger a random price change."""
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(select(Product).where(Product.is_active == True))
                products = result.scalars().all()
                if not products:
                    return

                product = random.choice(products)
                old_price = product.current_price

                # Random price adjustment (-10% to +10%)
                adjustment = Decimal(str(random.uniform(-0.10, 0.10)))
                new_price = product.current_price * (Decimal("1.00") + adjustment)
                new_price = new_price.quantize(Decimal("0.01"))

                product.current_price = new_price

                self.log_event(
                    "price_changed",
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "old_price": float(old_price),
                        "new_price": float(new_price),
                        "change_percent": float(adjustment * 100),
                    },
                )


# Global simulation instance
_simulation_engine: Optional[SimulationEngine] = None


def get_simulation_engine() -> SimulationEngine:
    """Get the global simulation engine instance."""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = SimulationEngine()
    return _simulation_engine
