"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch

from config import (
    Settings,
    get_settings,
    LLMProvider,
    LLMFactory,
    OpenAIModel,
    GeminiModel,
    ClaudeModel,
    LocalModel,
)


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        # Note: APP_ENV is set to 'test' in conftest.py for the test environment
        settings = Settings(
            openai_api_key="test-key",
            _env_file=None,  # Don't load .env file
        )

        assert settings.app_name == "NPC-Ecommerce-Sandbox"
        # APP_ENV inherits from environment set in conftest.py
        assert settings.app_env in ("development", "test")
        assert settings.debug is True
        assert settings.llm_provider == "openai"
        assert settings.llm_temperature == 0.7

    def test_settings_from_env(self):
        """Test settings loaded from environment variables."""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "TestApp",
                "APP_ENV": "production",
                "DEBUG": "false",
                "LLM_PROVIDER": "claude",
                "LLM_MODEL": "claude-sonnet-4-20250514",
            },
        ):
            settings = Settings(_env_file=None)
            assert settings.app_name == "TestApp"
            assert settings.app_env == "production"
            assert settings.debug is False
            assert settings.llm_provider == "claude"

    def test_database_url_settings(self):
        """Test database URL configuration."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/testdb",
            database_sync_url="postgresql://user:pass@localhost/testdb",
            _env_file=None,
        )

        assert "postgresql" in settings.database_url
        assert "asyncpg" in settings.database_url
        assert "localhost" in settings.database_sync_url


class TestLLMProvider:
    """Tests for LLMProvider enum."""

    def test_provider_values(self):
        """Test LLM provider enum values."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.GEMINI.value == "gemini"
        assert LLMProvider.CLAUDE.value == "claude"
        assert LLMProvider.LOCAL.value == "local"

    def test_provider_from_string(self):
        """Test creating provider from string."""
        assert LLMProvider("openai") == LLMProvider.OPENAI
        assert LLMProvider("gemini") == LLMProvider.GEMINI
        assert LLMProvider("claude") == LLMProvider.CLAUDE
        assert LLMProvider("local") == LLMProvider.LOCAL

    def test_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError):
            LLMProvider("invalid")


class TestLLMFactory:
    """Tests for LLMFactory class."""

    def test_create_openai_model(self):
        """Test creating OpenAI model."""
        model = LLMFactory.create(
            provider="openai",
            model="gpt-4o",
            api_key="test-key",
            temperature=0.5,
        )

        assert isinstance(model, OpenAIModel)
        assert model.model == "gpt-4o"
        assert model.api_key == "test-key"
        assert model.temperature == 0.5

    def test_create_gemini_model(self):
        """Test creating Gemini model."""
        model = LLMFactory.create(
            provider=LLMProvider.GEMINI,
            model="gemini-1.5-pro",
            api_key="test-key",
        )

        assert isinstance(model, GeminiModel)
        assert model.model == "gemini-1.5-pro"

    def test_create_claude_model(self):
        """Test creating Claude model."""
        model = LLMFactory.create(
            provider="claude",
            model="claude-sonnet-4-20250514",
            api_key="test-key",
        )

        assert isinstance(model, ClaudeModel)
        assert model.model == "claude-sonnet-4-20250514"

    def test_create_local_model(self):
        """Test creating local model."""
        model = LLMFactory.create(
            provider="local",
            model="llama3.2",
            base_url="http://localhost:11434/v1",
        )

        assert isinstance(model, LocalModel)
        assert model.model == "llama3.2"
        assert model.base_url == "http://localhost:11434/v1"

    def test_create_with_default_model(self):
        """Test creating model with default model name."""
        model = LLMFactory.create(provider="openai", api_key="test-key")
        assert model.model == "gpt-4o"

        model = LLMFactory.create(provider="claude", api_key="test-key")
        assert model.model == "claude-sonnet-4-20250514"

    def test_create_invalid_provider(self):
        """Test creating model with invalid provider."""
        with pytest.raises(ValueError, match="(Unsupported LLM provider|is not a valid LLMProvider)"):
            LLMFactory.create(provider="invalid", api_key="test-key")

    def test_list_providers(self):
        """Test listing available providers."""
        providers = LLMFactory.list_providers()

        assert "openai" in providers
        assert "gemini" in providers
        assert "claude" in providers
        assert "local" in providers
        assert len(providers) == 4

    def test_get_default_model(self):
        """Test getting default model for provider."""
        assert LLMFactory.get_default_model("openai") == "gpt-4o"
        assert LLMFactory.get_default_model("gemini") == "gemini-1.5-pro"
        assert LLMFactory.get_default_model("claude") == "claude-sonnet-4-20250514"
        assert LLMFactory.get_default_model("local") == "llama3.2"

    def test_from_settings(self):
        """Test creating model from settings."""
        settings = Settings(
            llm_provider="openai",
            llm_model="gpt-4o",
            llm_temperature=0.8,
            openai_api_key="test-key",
            _env_file=None,
        )

        model = LLMFactory.from_settings(settings)

        assert isinstance(model, OpenAIModel)
        assert model.model == "gpt-4o"
        assert model.temperature == 0.8
        assert model.api_key == "test-key"


class TestModelRepr:
    """Tests for model string representation."""

    def test_model_repr(self):
        """Test model __repr__ method."""
        model = LLMFactory.create(
            provider="openai",
            model="gpt-4o",
            api_key="test-key",
            temperature=0.7,
        )

        repr_str = repr(model)
        assert "OpenAIModel" in repr_str
        assert "gpt-4o" in repr_str
        assert "0.7" in repr_str
