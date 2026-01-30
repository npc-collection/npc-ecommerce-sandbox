"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

from .routes import agents_router, ecommerce_router, simulation_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.app_name}...")

    # Initialize database connection pool
    # Initialize Redis connection
    # Initialize agent systems

    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    # Clean up resources


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="NPC E-commerce Sandbox - Multi-agent simulation platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(agents_router)
    app.include_router(simulation_router)
    app.include_router(ecommerce_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "agents": "ready",
        }

    return app


# Application instance
app = create_app()
