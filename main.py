#!/usr/bin/env python
"""Main entry point for NPC E-commerce Sandbox."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import uvicorn


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def run_api():
    """Run the FastAPI server."""
    from config import get_settings

    settings = get_settings()
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


def run_dashboard():
    """Run the Streamlit dashboard."""
    from config import get_settings

    settings = get_settings()
    dashboard_path = get_project_root() / "dashboard" / "app.py"

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(settings.streamlit_port),
        "--server.headless", "true",
    ])


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NPC E-commerce Sandbox")
    parser.add_argument(
        "command",
        choices=["api", "dashboard", "all", "migrate"],
        help="Command to run",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )

    args = parser.parse_args()

    if args.command == "api":
        print("Starting API server...")
        run_api()

    elif args.command == "dashboard":
        print("Starting Streamlit dashboard...")
        run_dashboard()

    elif args.command == "all":
        print("Starting API server and dashboard...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(run_api)
            executor.submit(run_dashboard)

    elif args.command == "migrate":
        print("Running database migrations...")
        print("Migrations not yet implemented. Run: alembic upgrade head")


if __name__ == "__main__":
    main()
