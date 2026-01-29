# NPC E-commerce Sandbox

A multi-agent simulation platform for e-commerce operations using CrewAI and AutoGen.

## Architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.11+ | Single language for all components |
| Agent Orchestration | CrewAI | Multi-agent framework for inventory, pricing, and order agents |
| LLM Agent | AutoGen | Support agent for customer interactions |
| Backend / API | FastAPI | Async API layer for simulation and agent endpoints |
| Database | PostgreSQL | Persistent storage for sandbox data |
| Messaging / Queue | Redis | Async communication between agents |
| Simulation | Python modules | Custom environment for orders, inventory, pricing |
| Dashboard | Streamlit | Real-time monitoring dashboard |

## Project Structure

```
npc-ecommerce-sandbox/
├── main.py                 # Entry point
├── src/npc_ecommerce_sandbox/
│   ├── agents/
│   │   ├── crew/           # CrewAI agents (inventory, pricing, order)
│   │   │   ├── config/     # YAML configs for agents and tasks
│   │   │   ├── crew.py     # Crew definitions
│   │   │   └── tools.py    # Custom agent tools
│   │   └── autogen/        # AutoGen support agent
│   │       └── support_agent.py
│   ├── api/
│   │   ├── routes/         # FastAPI route handlers
│   │   └── app.py          # FastAPI application
│   ├── db/
│   │   └── models/         # SQLAlchemy models
│   ├── simulation/
│   │   ├── engine.py       # Simulation engine
│   │   └── scenarios.py    # Pre-defined scenarios
│   ├── messaging/
│   │   └── event_bus.py    # Redis pub/sub event bus
│   ├── dashboard/
│   │   └── app.py          # Streamlit dashboard
│   └── config/
│       └── settings.py     # Application settings
├── tests/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for PostgreSQL and Redis)
- OpenAI API key

### Installation

1. **Clone and navigate to project:**
   ```bash
   cd npc-ecommerce-sandbox
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Start infrastructure (PostgreSQL + Redis):**
   ```bash
   docker-compose up -d postgres redis
   ```

### Running the Application

**Start the API server:**
```bash
python main.py api
```

**Start the Streamlit dashboard:**
```bash
python main.py dashboard
```

**Or start both together:**
```bash
python main.py all
```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **pgAdmin** (optional): http://localhost:5050
- **Redis Commander** (optional): http://localhost:8081

## Agents

### CrewAI Agents

1. **Inventory Agent**
   - Monitors stock levels
   - Identifies reorder needs
   - Handles low stock alerts

2. **Pricing Agent**
   - Dynamic pricing optimization
   - Demand-based adjustments
   - Competitor response

3. **Order Agent**
   - Order processing
   - Inventory reservation
   - Status management

### AutoGen Support Agent

- Natural language customer support
- Order lookups
- Return processing
- Loyalty points management
- Discount code application

## Simulation

The simulation engine generates realistic e-commerce events:

- **Orders**: Random order generation with configurable rate
- **Inventory Events**: Stock alerts and depletion
- **Price Changes**: Dynamic pricing adjustments

### Scenarios

- Normal Operations
- Flash Sale
- Supply Shortage
- Seasonal Peak
- Competitor Price War
- New Product Launch

## API Endpoints

### Agents
- `POST /agents/inventory/check` - Run inventory check
- `POST /agents/orders/process` - Process an order
- `POST /agents/support/message` - Customer support query

### Simulation
- `POST /simulation/start` - Start simulation
- `POST /simulation/stop` - Stop simulation
- `GET /simulation/status` - Get simulation status
- `POST /simulation/trigger/order` - Generate random order

### E-commerce
- `GET /ecommerce/products` - List products
- `GET /ecommerce/inventory` - List inventory
- `GET /ecommerce/orders` - List orders
- `GET /ecommerce/dashboard/stats` - Dashboard statistics

## Development

### Run tests
```bash
pytest
```

### Format code
```bash
black src tests
ruff check src tests
```

### Type checking
```bash
mypy src
```

## Configuration

All settings can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | - | OpenAI API key (required) |
| DATABASE_URL | postgresql+asyncpg://... | PostgreSQL connection |
| REDIS_URL | redis://localhost:6379/0 | Redis connection |
| API_PORT | 8000 | FastAPI port |
| STREAMLIT_PORT | 8501 | Dashboard port |
| LLM_MODEL | gpt-4o | LLM model for agents |
| AGENT_VERBOSE | true | Verbose agent output |

## License

MIT
