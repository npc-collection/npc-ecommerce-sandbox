# CLAUDE.md - AI Assistant Guide for NPC E-commerce Sandbox

This document provides essential context for AI assistants working with this codebase.

## Project Overview

NPC E-commerce Sandbox is a **multi-agent simulation platform** for e-commerce operations. It combines:
- **CrewAI** for orchestrating inventory, pricing, and order management agents
- **AutoGen** for customer support interactions
- **FastAPI** for the REST API layer
- **PostgreSQL** for persistent storage
- **Redis** for async messaging between agents
- **Streamlit** for real-time monitoring dashboard

**Python Version**: 3.11+ (supports 3.11, 3.12, 3.13)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI (api/)                          │
│  /agents/* - Agent endpoints                                    │
│  /simulation/* - Simulation control                             │
│  /ecommerce/* - Product, inventory, order queries               │
├─────────────────────────────────────────────────────────────────┤
│                       Agent Layer                               │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │   CrewAI (agents/crew/) │  │  AutoGen (agents/autogen/)  │  │
│  │  - Inventory Agent      │  │  - Support Agent            │  │
│  │  - Pricing Agent        │  │  - Triage Agent             │  │
│  │  - Order Agent          │  │  - Technical Agent          │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                  Event Bus (messaging/)                         │
│              Redis pub/sub for agent communication              │
├─────────────────────────────────────────────────────────────────┤
│    Simulation Engine (simulation/)   │   Database (db/)        │
│    - Order generation                │   - SQLAlchemy models   │
│    - Inventory events                │   - Async sessions      │
│    - Price changes                   │   - PostgreSQL          │
│    - Scenario support                │                         │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
npc-ecommerce-sandbox/
├── api/                    # FastAPI application
│   ├── app.py              # App factory and middleware
│   └── routes/             # API route handlers
│       ├── agents.py       # /agents/* endpoints
│       ├── ecommerce.py    # /ecommerce/* endpoints
│       └── simulation.py   # /simulation/* endpoints
├── agents/                 # Multi-agent implementations
│   ├── crew/               # CrewAI agents
│   │   ├── crew.py         # Crew and agent definitions
│   │   └── tools.py        # Custom agent tools
│   └── autogen/            # AutoGen agents
│       └── support_agent.py # Customer support agent
├── config/                 # Configuration
│   ├── settings.py         # Pydantic settings (env vars)
│   └── llm_models.py       # LLM provider abstraction
├── db/                     # Database layer
│   ├── init.py             # Database initialization
│   └── models/             # SQLAlchemy models
│       ├── base.py         # Base model with timestamps
│       └── ecommerce.py    # Product, Order, Inventory, etc.
├── messaging/              # Event bus
│   └── event_bus.py        # Redis pub/sub implementation
├── simulation/             # Simulation engine
│   ├── engine.py           # SimulationEngine class
│   └── scenarios.py        # Predefined scenarios
├── dashboard/              # Streamlit dashboard
│   └── app.py              # Dashboard application
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api.py         # API endpoint tests
│   ├── test_models.py      # Database model tests
│   ├── test_simulation.py  # Simulation tests
│   └── ...
├── main.py                 # CLI entry point
├── pyproject.toml          # Project config and dependencies
├── Makefile                # Development commands
├── docker-compose.yml      # Docker services
└── Dockerfile              # Production image
```

## Key Files to Understand

| File | Purpose |
|------|---------|
| `config/settings.py` | All environment variables and defaults |
| `config/llm_models.py` | LLM provider abstraction (OpenAI, Claude, Gemini, Local) |
| `api/app.py` | FastAPI app creation and middleware setup |
| `db/models/ecommerce.py` | Core data models (Product, Order, Inventory, Customer) |
| `simulation/engine.py` | SimulationEngine - generates e-commerce events |
| `agents/crew/crew.py` | CrewAI agent definitions and crews |
| `agents/autogen/support_agent.py` | AutoGen customer support implementation |
| `messaging/event_bus.py` | Redis pub/sub event system |

## Development Setup

### Quick Start
```bash
# 1. Create virtual environment
python -m venv venv && source venv/bin/activate

# 2. Install dev dependencies
pip install -e ".[dev]"

# 3. Copy environment file
cp .env.example .env
# Edit .env and set LLM_PROVIDER and API keys

# 4. Start infrastructure
docker compose up -d postgres redis

# 5. Initialize database (optional)
python -m db.init

# 6. Run API server
python main.py api
```

### Using Makefile
```bash
make dev          # Install deps + start infrastructure
make run-api      # Start API server (uvicorn with reload)
make run-dash     # Start Streamlit dashboard
make test         # Run test suite
make lint         # Run ruff + mypy
make format       # Format with black + ruff --fix
make clean        # Remove cache files
```

## Testing

### Running Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=api,config,db,simulation,messaging

# Skip integration tests
pytest tests/ -m "not integration"

# Specific test file
pytest tests/test_api.py -v
```

### Test Configuration
- Tests use **SQLite in-memory** database (see `conftest.py`)
- Environment is automatically set to `test` mode
- LLM calls are mocked - see `mock_llm_client` and `mock_autogen_client` fixtures
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`

### Key Test Fixtures (in `tests/conftest.py`)
- `test_settings` - Test configuration
- `sync_session` / `async_session` - Database sessions
- `sample_products` / `sample_customers` - Test data
- `seeded_database` - Database with test data
- `client` / `test_client` - FastAPI TestClient
- `mock_llm_client` - Mocked LLM responses

## Code Style and Conventions

### Python Style
- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff (rules: E, F, I, N, W, UP)
- **Type hints**: Required (mypy strict mode, but `ignore_missing_imports = true`)

### Naming Conventions
- Models: `PascalCase` (e.g., `Product`, `OrderItem`)
- Functions/methods: `snake_case` (e.g., `get_settings`, `run_inventory_check`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODELS`)
- Enums: `PascalCase` class with `UPPER_SNAKE_CASE` values

### Import Order (enforced by ruff)
1. Standard library
2. Third-party packages
3. Local imports

### Database Patterns
- Use SQLAlchemy 2.0 style with `Mapped` type annotations
- All models inherit from `Base` and `TimestampMixin`
- Use async sessions for API routes (`create_async_engine`, `AsyncSession`)
- Sync sessions available for CLI/scripts

### API Patterns
- Use Pydantic models for request/response validation
- Raise `HTTPException` for error responses
- Agent imports are lazy (inside route functions) to avoid startup issues

## LLM Configuration

The project supports multiple LLM providers via `config/llm_models.py`:

| Provider | Env Variable | Default Model |
|----------|--------------|---------------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o |
| Anthropic Claude | `CLAUDE_API_KEY` | claude-sonnet-4-20250514 |
| Google Gemini | `GEMINI_API_KEY` | gemini-1.5-pro |
| Local (Ollama) | `LLM_BASE_URL` | llama3.2 |

Set `LLM_PROVIDER` in `.env` to switch providers. The `LLMFactory` creates appropriate clients for both CrewAI and AutoGen frameworks.

## Common Tasks

### Adding a New API Endpoint
1. Create/modify route in `api/routes/`
2. Add Pydantic request/response models
3. Register router in `api/app.py` if new file
4. Add tests in `tests/test_api.py`

### Adding a New Agent (CrewAI)
1. Define agent in `agents/crew/crew.py` using `@agent` decorator
2. Add tools in `agents/crew/tools.py`
3. Create tasks using `@task` decorator
4. Compose into a `Crew` using `@crew` decorator

### Adding a New Agent (AutoGen)
1. Create agent function in `agents/autogen/support_agent.py`
2. Define tools using `FunctionTool`
3. Create `AssistantAgent` with tools and system message
4. Optionally add to team (SelectorGroupChat/RoundRobinGroupChat)

### Adding a New Database Model
1. Create model in `db/models/ecommerce.py`
2. Inherit from `Base` and `TimestampMixin`
3. Use `Mapped[]` for column types
4. Add relationships with `relationship()`
5. Import in `db/models/__init__.py`

### Adding a New Simulation Scenario
1. Add scenario config in `simulation/scenarios.py`
2. Define `ScenarioConfig` with rate multipliers and special behaviors
3. Add to `SCENARIOS` dict

## Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | openai, claude, gemini, or local |
| `LLM_MODEL` | No | Model name (uses provider default) |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `CLAUDE_API_KEY` | If using Claude | Anthropic API key |
| `DATABASE_URL` | No | PostgreSQL async URL |
| `REDIS_URL` | No | Redis connection URL |
| `DEBUG` | No | Enable debug mode (default: true) |

## Docker

### Development (infrastructure only)
```bash
docker compose up -d postgres redis
```

### Production (full stack)
```bash
docker compose --profile prod up -d
```

### Admin tools (pgAdmin, Redis Commander)
```bash
docker compose --profile admin up -d
```

## CI/CD (GitHub Actions)

The CI pipeline (`.github/workflows/ci.yml`) runs:
1. **Lint & Format Check** - black, ruff, mypy
2. **Test** - pytest on Python 3.11, 3.12, 3.13
3. **Integration Tests** - with real PostgreSQL and Redis
4. **Security Scan** - bandit, safety
5. **Build Package** - hatchling build
6. **Docker Build** - on main branch pushes

## Troubleshooting

### "No customers or products in database"
Run database initialization: `python -m db.init`

### Agent LLM errors
1. Check `LLM_PROVIDER` matches your API key
2. Ensure API key is set in `.env`
3. For local models, verify `LLM_BASE_URL` is correct

### Redis connection failed
The event bus falls back to local mode if Redis is unavailable. For full functionality, ensure Redis is running: `docker compose up -d redis`

### Import errors in tests
Tests set environment variables before imports (see `conftest.py`). Ensure you're running tests with pytest, not directly.

## Important Notes for AI Assistants

1. **Always read existing code** before making changes
2. **Run tests** after modifications: `make test`
3. **Format code** before committing: `make format`
4. **Check types** for significant changes: `make lint`
5. **Use lazy imports** for agents in API routes to avoid circular imports
6. **Mock LLM calls** in tests - never make real API calls
7. **Use async patterns** consistently in API layer
8. **Prefer editing existing files** over creating new ones
9. **Keep changes minimal** - don't over-engineer solutions
10. **Test coverage minimum**: 60% (enforced in pyproject.toml)
