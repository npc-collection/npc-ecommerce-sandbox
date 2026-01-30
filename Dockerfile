# Production Dockerfile for NPC E-commerce Sandbox
# Mirrors the local development environment exactly

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies (production only, no dev deps)
RUN pip install --upgrade pip && \
    pip install .

# Copy application code
COPY api/ ./api/
COPY agents/ ./agents/
COPY config/ ./config/
COPY db/ ./db/
COPY messaging/ ./messaging/
COPY simulation/ ./simulation/
COPY dashboard/ ./dashboard/
COPY main.py ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
