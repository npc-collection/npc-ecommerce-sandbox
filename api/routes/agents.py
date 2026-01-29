"""API routes for agent interactions."""

from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["agents"])


class InventoryCheckRequest(BaseModel):
    """Request model for inventory check."""

    inventory_data: dict = Field(default_factory=dict)


class OrderProcessRequest(BaseModel):
    """Request model for order processing."""

    order_data: dict


class SupportMessageRequest(BaseModel):
    """Request model for customer support."""

    message: str
    customer_email: Optional[str] = None


class AgentResponse(BaseModel):
    """Response model for agent tasks."""

    success: bool
    result: str
    task_id: Optional[str] = None


@router.post("/inventory/check", response_model=AgentResponse)
async def check_inventory(request: InventoryCheckRequest):
    """Run inventory check with CrewAI agents."""
    try:
        from agents import run_inventory_check

        result = run_inventory_check(request.inventory_data)
        return AgentResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/process", response_model=AgentResponse)
async def process_order(request: OrderProcessRequest):
    """Process an order with CrewAI agents."""
    try:
        from agents import run_order_processing

        result = run_order_processing(request.order_data)
        return AgentResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support/message", response_model=AgentResponse)
async def handle_support_message(request: SupportMessageRequest):
    """Handle a customer support message with AutoGen agents."""
    try:
        from agents import handle_customer_message

        result = await handle_customer_message(
            message=request.message,
            customer_email=request.customer_email,
        )
        return AgentResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support/simple", response_model=AgentResponse)
async def simple_support(request: SupportMessageRequest):
    """Handle a simple support query with single AutoGen agent."""
    try:
        from agents import run_simple_support

        result = await run_simple_support(request.message)
        return AgentResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agents_health():
    """Check agent system health."""
    return {
        "status": "healthy",
        "agents": {
            "crewai": {
                "inventory_agent": "ready",
                "pricing_agent": "ready",
                "order_agent": "ready",
            },
            "autogen": {
                "support_agent": "ready",
                "triage_agent": "ready",
                "technical_agent": "ready",
            },
        },
    }
