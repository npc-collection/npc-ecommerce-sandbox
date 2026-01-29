"""API routes module."""

from .agents import router as agents_router
from .simulation import router as simulation_router
from .ecommerce import router as ecommerce_router

__all__ = ["agents_router", "simulation_router", "ecommerce_router"]
