"""LLM model providers for agent support."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LOCAL = "local"


# Default models for each provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.GEMINI: "gemini-1.5-pro",
    LLMProvider.CLAUDE: "claude-sonnet-4-20250514",
    LLMProvider.LOCAL: "llama3.2",
}


class BaseLLMModel(ABC):
    """Base class for LLM model implementations."""

    provider: LLMProvider

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        """Initialize the LLM model.

        Args:
            model: The model name/identifier
            temperature: Sampling temperature
            api_key: API key for the provider
            base_url: Base URL for API calls (for local models)
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs

    @abstractmethod
    def get_autogen_client(self) -> Any:
        """Get the AutoGen-compatible model client.

        Returns:
            Model client compatible with AutoGen framework
        """
        pass

    @abstractmethod
    def get_crewai_llm(self) -> Any:
        """Get the CrewAI-compatible LLM instance.

        Returns:
            LLM instance compatible with CrewAI framework
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r}, temperature={self.temperature})"


class OpenAIModel(BaseLLMModel):
    """OpenAI model implementation."""

    provider = LLMProvider.OPENAI

    def get_autogen_client(self) -> Any:
        """Get OpenAI client for AutoGen."""
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        return OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs,
        )

    def get_crewai_llm(self) -> Any:
        """Get OpenAI LLM for CrewAI."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs,
        )


class GeminiModel(BaseLLMModel):
    """Google Gemini model implementation."""

    provider = LLMProvider.GEMINI

    def get_autogen_client(self) -> Any:
        """Get Gemini client for AutoGen."""
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        # Gemini can be accessed via OpenAI-compatible endpoint
        return OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=self.temperature,
            **self.kwargs,
        )

    def get_crewai_llm(self) -> Any:
        """Get Gemini LLM for CrewAI."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs,
        )


class ClaudeModel(BaseLLMModel):
    """Anthropic Claude model implementation."""

    provider = LLMProvider.CLAUDE

    def get_autogen_client(self) -> Any:
        """Get Claude client for AutoGen."""
        from autogen_ext.models.anthropic import AnthropicChatCompletionClient

        return AnthropicChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs,
        )

    def get_crewai_llm(self) -> Any:
        """Get Claude LLM for CrewAI."""
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=self.model,
            anthropic_api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs,
        )


class LocalModel(BaseLLMModel):
    """Local model implementation (e.g., Ollama, LM Studio, vLLM)."""

    provider = LLMProvider.LOCAL

    def get_autogen_client(self) -> Any:
        """Get local model client for AutoGen."""
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        # Local models typically use OpenAI-compatible API
        return OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key or "local",  # Some local servers don't need API key
            base_url=self.base_url or "http://localhost:11434/v1",  # Default Ollama URL
            temperature=self.temperature,
            **self.kwargs,
        )

    def get_crewai_llm(self) -> Any:
        """Get local model LLM for CrewAI."""
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=self.model,
            base_url=self.base_url or "http://localhost:11434",
            temperature=self.temperature,
            **self.kwargs,
        )


class LLMFactory:
    """Factory for creating LLM model instances."""

    _model_classes: dict[LLMProvider, type[BaseLLMModel]] = {
        LLMProvider.OPENAI: OpenAIModel,
        LLMProvider.GEMINI: GeminiModel,
        LLMProvider.CLAUDE: ClaudeModel,
        LLMProvider.LOCAL: LocalModel,
    }

    @classmethod
    def create(
        cls,
        provider: LLMProvider | str,
        model: str | None = None,
        temperature: float = 0.7,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> BaseLLMModel:
        """Create an LLM model instance.

        Args:
            provider: The LLM provider to use (string or enum)
            model: The model name/identifier. If None, uses default for provider.
            temperature: Sampling temperature
            api_key: API key for the provider
            base_url: Base URL for API calls (for local models)
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM model instance

        Raises:
            ValueError: If provider is not supported
        """
        # Convert string to enum if needed
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        if provider not in cls._model_classes:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Use default model if not specified
        if model is None:
            model = DEFAULT_MODELS[provider]

        model_class = cls._model_classes[provider]
        return model_class(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    @classmethod
    def from_settings(cls, settings) -> BaseLLMModel:
        """Create an LLM model from settings.

        Args:
            settings: Application settings instance

        Returns:
            LLM model instance configured from settings
        """
        provider = LLMProvider(settings.llm_provider.lower())

        # Get the appropriate API key based on provider
        api_key_map = {
            LLMProvider.OPENAI: settings.openai_api_key,
            LLMProvider.GEMINI: settings.gemini_api_key,
            LLMProvider.CLAUDE: settings.claude_api_key,
            LLMProvider.LOCAL: settings.local_api_key,
        }

        api_key = api_key_map.get(provider)

        return cls.create(
            provider=provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=api_key,
            base_url=settings.llm_base_url if provider == LLMProvider.LOCAL else None,
        )

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all supported LLM providers.

        Returns:
            List of provider names
        """
        return [p.value for p in LLMProvider]

    @classmethod
    def get_default_model(cls, provider: LLMProvider | str) -> str:
        """Get the default model for a provider.

        Args:
            provider: The LLM provider

        Returns:
            Default model name for the provider
        """
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())
        return DEFAULT_MODELS[provider]
