"""Application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "NPC-Ecommerce-Sandbox"
    app_env: str = "development"
    debug: bool = True

    # LLM Provider Configuration
    llm_provider: str = "openai"  # Options: openai, gemini, claude, local
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_base_url: str | None = None  # For local models (e.g., http://localhost:11434/v1)

    # API Keys for different providers
    openai_api_key: str = ""
    gemini_api_key: str = ""
    claude_api_key: str = ""
    local_api_key: str = ""  # Optional, some local servers don't need it

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/npc_ecommerce"
    database_sync_url: str = "postgresql://postgres:postgres@localhost:5432/npc_ecommerce"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Streamlit
    streamlit_port: int = 8501

    # Agent Settings
    agent_verbose: bool = True
    agent_max_iter: int = 15
    agent_max_rpm: int = 10


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
