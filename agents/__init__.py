"""Agents module combining CrewAI and AutoGen agents."""

from .crew import (
    EcommerceCrew,
    run_inventory_check,
    run_order_processing,
)
from .autogen import (
    create_support_agent,
    create_support_team,
    handle_customer_message,
    run_simple_support,
)

__all__ = [
    # CrewAI agents
    "EcommerceCrew",
    "run_inventory_check",
    "run_order_processing",
    # AutoGen agents
    "create_support_agent",
    "create_support_team",
    "handle_customer_message",
    "run_simple_support",
]
