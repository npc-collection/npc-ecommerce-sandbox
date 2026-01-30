"""
Tests for NPC E-commerce Sandbox.

Test Structure:
- test_config.py: Configuration and LLM factory tests
- test_models.py: Database model tests
- test_scenarios.py: Simulation scenario tests
- test_simulation.py: Simulation engine tests
- test_api.py: FastAPI endpoint tests

Run tests with:
    pytest tests/ -v

Run with coverage:
    pytest tests/ -v --cov=api --cov=agents --cov=config \
        --cov=db --cov=simulation --cov=messaging --cov-report=html

Run specific test file:
    pytest tests/test_api.py -v

Run tests in parallel:
    pytest tests/ -n auto
"""
