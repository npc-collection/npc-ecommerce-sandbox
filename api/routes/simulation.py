"""API routes for simulation control."""

from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from npc_ecommerce_sandbox.simulation import (
    SimulationEngine,
    get_simulation_engine,
    generate_random_order,
    trigger_low_stock_event,
    trigger_price_change_event,
    ScenarioType,
    list_scenarios,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationConfig(BaseModel):
    """Configuration for simulation run."""

    scenario: str = Field(
        default="normal_operations",
        description="Scenario type: normal_operations, flash_sale, supply_shortage, "
        "seasonal_peak, competitor_price_war, new_product_launch, demand_spike, slow_period",
    )
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    order_rate_per_minute: float = Field(default=2.0, ge=0.1, le=100)
    include_price_changes: bool = True
    include_inventory_events: bool = True
    random_seed: Optional[int] = None


class SimulationStatus(BaseModel):
    """Status of a simulation run."""

    running: bool
    scenario: Optional[str] = None
    elapsed_minutes: float
    total_orders: int
    total_revenue: float
    inventory_alerts: int
    price_changes: int


class ScenarioInfo(BaseModel):
    """Information about a simulation scenario."""

    type: str
    name: str
    description: str
    duration_minutes: int
    order_rate_multiplier: float


# Global simulation state
_simulation_state = {
    "running": False,
    "scenario": None,
    "config": None,
    "stats": {
        "elapsed_minutes": 0,
        "total_orders": 0,
        "total_revenue": 0.0,
        "inventory_alerts": 0,
        "price_changes": 0,
    },
}


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def get_scenarios():
    """List all available simulation scenarios."""
    return list_scenarios()


@router.post("/start")
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a new simulation run with the specified scenario."""
    if _simulation_state["running"]:
        raise HTTPException(status_code=400, detail="Simulation already running")

    # Validate scenario
    try:
        ScenarioType(config.scenario)
    except ValueError:
        valid = [s.value for s in ScenarioType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{config.scenario}'. Valid options: {valid}",
        )

    _simulation_state["running"] = True
    _simulation_state["scenario"] = config.scenario
    _simulation_state["config"] = config.model_dump()
    _simulation_state["stats"] = {
        "elapsed_minutes": 0,
        "total_orders": 0,
        "total_revenue": 0.0,
        "inventory_alerts": 0,
        "price_changes": 0,
    }

    # Start simulation in background
    background_tasks.add_task(run_simulation_background, config)

    return {
        "message": f"Simulation started with scenario: {config.scenario}",
        "config": config.model_dump(),
    }


@router.post("/stop")
async def stop_simulation():
    """Stop the current simulation."""
    if not _simulation_state["running"]:
        raise HTTPException(status_code=400, detail="No simulation running")

    engine = get_simulation_engine()
    engine.stop()

    _simulation_state["running"] = False

    return {
        "message": "Simulation stopped",
        "stats": _simulation_state["stats"],
    }


@router.get("/status", response_model=SimulationStatus)
async def get_simulation_status():
    """Get current simulation status."""
    engine = get_simulation_engine()
    status = engine.get_status()

    return SimulationStatus(
        running=_simulation_state["running"],
        scenario=_simulation_state["scenario"],
        elapsed_minutes=status.get("elapsed_minutes", 0),
        total_orders=status.get("orders_generated", 0),
        total_revenue=status.get("total_revenue", 0.0),
        inventory_alerts=status.get("inventory_alerts", 0),
        price_changes=status.get("price_changes", 0),
    )


@router.get("/events")
async def get_recent_events(limit: int = Query(default=20, ge=1, le=100)):
    """Get recent simulation events."""
    engine = get_simulation_engine()
    status = engine.get_status()
    events = status.get("recent_events", [])

    return {
        "count": len(events),
        "events": events[-limit:],
    }


@router.post("/trigger/order")
async def trigger_order():
    """Manually trigger a simulated order."""
    try:
        order = await generate_random_order()
        if "error" in order:
            raise HTTPException(status_code=400, detail=order["error"])
        return {"message": "Order generated", "order": order}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/inventory-alert")
async def trigger_inventory_alert(product_sku: str):
    """Manually trigger an inventory alert for testing."""
    try:
        result = await trigger_low_stock_event(product_sku)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"message": "Inventory alert triggered", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/price-change")
async def trigger_price_change(
    product_sku: str,
    change_percent: float = Query(..., ge=-50, le=50, description="Price change percentage"),
):
    """Manually trigger a price change event."""
    try:
        result = await trigger_price_change_event(product_sku, change_percent)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"message": "Price change triggered", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_simulation_background(config: SimulationConfig):
    """Run the simulation in the background."""
    engine = SimulationEngine(
        order_rate=config.order_rate_per_minute,
        include_price_changes=config.include_price_changes,
        include_inventory_events=config.include_inventory_events,
        random_seed=config.random_seed,
    )

    try:
        async for event in engine.run(
            duration_minutes=config.duration_minutes,
            scenario=config.scenario,
        ):
            if not _simulation_state["running"]:
                break

            # Update stats
            elapsed = event.get("elapsed_minutes", event.get("data", {}).get("elapsed_minutes", 0))
            _simulation_state["stats"]["elapsed_minutes"] = elapsed

            event_type = event.get("type")
            if event_type == "order":
                _simulation_state["stats"]["total_orders"] += 1
                _simulation_state["stats"]["total_revenue"] += event.get("data", {}).get(
                    "amount", 0
                )
            elif event_type == "inventory_alert":
                _simulation_state["stats"]["inventory_alerts"] += 1
            elif event_type == "price_change":
                _simulation_state["stats"]["price_changes"] += 1

    finally:
        _simulation_state["running"] = False
