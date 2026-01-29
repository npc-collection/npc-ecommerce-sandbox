"""API routes for simulation control."""

from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationConfig(BaseModel):
    """Configuration for simulation run."""

    duration_minutes: int = Field(default=60, ge=1, le=1440)
    order_rate_per_minute: float = Field(default=2.0, ge=0.1, le=100)
    include_price_changes: bool = True
    include_inventory_events: bool = True
    random_seed: Optional[int] = None


class SimulationStatus(BaseModel):
    """Status of a simulation run."""

    running: bool
    elapsed_minutes: float
    total_orders: int
    total_revenue: float
    inventory_alerts: int
    price_changes: int


# Global simulation state (in production, use Redis or database)
_simulation_state = {
    "running": False,
    "config": None,
    "stats": {
        "elapsed_minutes": 0,
        "total_orders": 0,
        "total_revenue": 0.0,
        "inventory_alerts": 0,
        "price_changes": 0,
    },
}


@router.post("/start")
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a new simulation run."""
    if _simulation_state["running"]:
        raise HTTPException(status_code=400, detail="Simulation already running")

    _simulation_state["running"] = True
    _simulation_state["config"] = config.model_dump()

    # Start simulation in background
    background_tasks.add_task(run_simulation_background, config)

    return {"message": "Simulation started", "config": config.model_dump()}


@router.post("/stop")
async def stop_simulation():
    """Stop the current simulation."""
    if not _simulation_state["running"]:
        raise HTTPException(status_code=400, detail="No simulation running")

    _simulation_state["running"] = False
    return {"message": "Simulation stopped", "stats": _simulation_state["stats"]}


@router.get("/status", response_model=SimulationStatus)
async def get_simulation_status():
    """Get current simulation status."""
    return SimulationStatus(
        running=_simulation_state["running"],
        **_simulation_state["stats"],
    )


@router.post("/trigger/order")
async def trigger_order():
    """Manually trigger a simulated order."""
    try:
        from npc_ecommerce_sandbox.simulation import generate_random_order

        order = await generate_random_order()
        return {"message": "Order generated", "order": order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/inventory-alert")
async def trigger_inventory_alert(product_sku: str):
    """Manually trigger an inventory alert for testing."""
    try:
        from npc_ecommerce_sandbox.simulation import trigger_low_stock_event

        result = await trigger_low_stock_event(product_sku)
        return {"message": "Inventory alert triggered", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/price-change")
async def trigger_price_change(product_sku: str, change_percent: float):
    """Manually trigger a price change event."""
    try:
        from npc_ecommerce_sandbox.simulation import trigger_price_change_event

        result = await trigger_price_change_event(product_sku, change_percent)
        return {"message": "Price change triggered", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_simulation_background(config: SimulationConfig):
    """Run the simulation in the background."""
    import asyncio
    from npc_ecommerce_sandbox.simulation import SimulationEngine

    engine = SimulationEngine(
        order_rate=config.order_rate_per_minute,
        include_price_changes=config.include_price_changes,
        include_inventory_events=config.include_inventory_events,
        random_seed=config.random_seed,
    )

    try:
        async for event in engine.run(duration_minutes=config.duration_minutes):
            if not _simulation_state["running"]:
                break

            # Update stats
            _simulation_state["stats"]["elapsed_minutes"] = event.get("elapsed_minutes", 0)
            if event.get("type") == "order":
                _simulation_state["stats"]["total_orders"] += 1
                _simulation_state["stats"]["total_revenue"] += event.get("amount", 0)
            elif event.get("type") == "inventory_alert":
                _simulation_state["stats"]["inventory_alerts"] += 1
            elif event.get("type") == "price_change":
                _simulation_state["stats"]["price_changes"] += 1

    finally:
        _simulation_state["running"] = False
