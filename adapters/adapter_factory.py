"""
Adapter factory for creating the appropriate adapter based on model provider.
"""

from typing import Dict, Optional, Type

from adapters.anthropic_adapter import AnthropicAdapter
from adapters.base_adapter import BaseAdapter
from adapters.gemini_adapter import GeminiAdapter
from adapters.openai_adapter import OpenAIAdapter


class AdapterFactory:
    """Factory for creating model adapters."""

    # Registry of adapter classes by provider name
    _adapters: Dict[str, Type[BaseAdapter]] = {
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "openai": OpenAIAdapter,
    }

    @classmethod
    def create(cls, provider: str, api_key: str) -> BaseAdapter:
        """
        Create an adapter instance for the specified provider.

        Args:
            provider: The provider name (anthropic, gemini, openai)
            api_key: The API key for the provider

        Returns:
            BaseAdapter: An instance of the appropriate adapter

        Raises:
            ValueError: If the provider is not supported
        """
        provider = provider.lower()
        if provider not in cls._adapters:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Available providers: {', '.join(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[provider]
        return adapter_class(api_key)

    @classmethod
    def register(cls, provider: str, adapter_class: Type[BaseAdapter]) -> None:
        """
        Register a new adapter class.

        Args:
            provider: The provider name to register
            adapter_class: The adapter class to use for this provider
        """
        cls._adapters[provider.lower()] = adapter_class

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Get a list of supported providers.

        Returns:
            List[str]: Names of supported providers
        """
        return list(cls._adapters.keys())
