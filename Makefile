# NPC E-commerce Sandbox - Makefile

.PHONY: help install dev test lint format clean docker-up docker-down docker-prod docker-build

# Default target
help:
	@echo "NPC E-commerce Sandbox - Available Commands"
	@echo ""
	@echo "Development (local venv):"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev          - Install dev dependencies + start infra"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters (ruff, mypy)"
	@echo "  make format       - Format code (black, ruff)"
	@echo "  make run-api      - Run API server locally"
	@echo "  make run-dash     - Run dashboard locally"
	@echo "  make db-init      - Initialize database with seed data"
	@echo ""
	@echo "Docker Infrastructure:"
	@echo "  make docker-up    - Start postgres + redis"
	@echo "  make docker-down  - Stop all containers"
	@echo "  make docker-logs  - View container logs"
	@echo ""
	@echo "Docker Production:"
	@echo "  make docker-build - Build production image"
	@echo "  make docker-prod  - Run full stack in Docker"
	@echo "  make docker-admin - Start admin tools (pgadmin, redis-commander)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove Python cache files"
	@echo "  make clean-all    - Remove cache + Docker volumes"

# =============================================================================
# Development (Local venv)
# =============================================================================

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	docker compose up -d postgres redis
	@echo "Infrastructure started. Run 'make run-api' to start the API."

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=api --cov=agents --cov=config --cov=db --cov=simulation --cov=messaging --cov-report=html

lint:
	ruff check .
	mypy . --ignore-missing-imports

format:
	black .
	ruff check --fix .

run-api:
	uvicorn api:app --reload --host 0.0.0.0 --port 8000

run-dash:
	streamlit run dashboard/app.py --server.port 8501

db-init:
	python -m db.init

# =============================================================================
# Docker Infrastructure
# =============================================================================

docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# =============================================================================
# Docker Production
# =============================================================================

docker-build:
	docker compose build api dashboard

docker-prod:
	docker compose --profile prod up -d

docker-prod-down:
	docker compose --profile prod down

docker-admin:
	docker compose --profile admin up -d

# =============================================================================
# Cleanup
# =============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true

clean-all: clean docker-down
	docker volume rm npc-ecommerce-sandbox_postgres_data npc-ecommerce-sandbox_redis_data 2>/dev/null || true
