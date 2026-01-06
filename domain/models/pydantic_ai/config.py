"""
Configuration models for PydanticAI integration.

This module provides configuration models that extend PydanticAI's
configuration with Luna-specific settings.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_ai.models import KnownModelName, ModelSettings


class ProviderType(str, Enum):
    """Supported model providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    GROQ = "groq"
    COHERE = "cohere"


class LunaModelConfig(BaseModel):
    """
    Configuration for a model to be used with Luna.

    This combines provider selection with model-specific settings.
    """

    provider: ProviderType = Field(
        default=ProviderType.ANTHROPIC, description="The provider to use for this model"
    )

    model_name: str = Field(
        default="claude-sonnet-4-5", description="The specific model to use (provider-specific)"
    )

    max_tokens: int = Field(default=4000, description="Maximum tokens for this model's completion")

    temperature: float = Field(default=0.7, description="Temperature setting (0.0-1.0)")

    additional_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific settings"
    )

    def to_known_model_name(self) -> KnownModelName:
        """
        Convert to PydanticAI's KnownModelName format.

        Returns:
            KnownModelName: The model name in PydanticAI format
        """
        # Format is provider:model_name
        return f"{self.provider.value}:{self.model_name}"

    def to_model_settings(self) -> ModelSettings:
        """
        Convert to PydanticAI's ModelSettings.

        Returns:
            ModelSettings: The model settings in PydanticAI format
        """
        # Start with our standard settings
        settings = {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        # Add any provider-specific settings
        settings.update(self.additional_settings)

        return ModelSettings(**settings)


class LunaAgentConfig(BaseModel):
    """
    Configuration for a Luna agent using PydanticAI.

    This extends our existing agent configuration with PydanticAI-specific settings.
    """

    name: str = Field(description="The name of the agent")

    model_config: LunaModelConfig = Field(
        default_factory=LunaModelConfig, description="Configuration for the model to use"
    )

    system_prompt_file: Optional[str] = Field(
        default=None, description="Path to the system prompt file"
    )

    system_prompt: Optional[str] = Field(
        default=None, description="Inline system prompt (used if file not specified)"
    )

    allowed_tools: List[str] = Field(
        default_factory=list, description="List of tool names this agent can use"
    )

    description: Optional[str] = Field(
        default=None, description="Description of this agent's purpose"
    )

    features: Dict[str, Any] = Field(
        default_factory=dict, description="Feature flags for this agent"
    )

    retries: int = Field(default=1, description="Number of retries for tool calls")

    @field_validator("features")
    def validate_features(cls, features: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that required features exist."""
        if not features:
            raise ValueError("Features dictionary is required in agent config")

        if "persona_config" not in features:
            raise ValueError("persona_config is required in features")

        if "cognitive" not in features:
            raise ValueError("cognitive flag is required in features")

        if features.get("cognitive", False) and "cognitive_structure" not in features:
            raise ValueError("cognitive_structure is required when cognitive is true")

        return features


class LunaAppConfig(BaseModel):
    """
    Application-level configuration for Luna with PydanticAI.

    This combines all configuration options for the Luna application.
    """

    default_model: LunaModelConfig = Field(
        default_factory=LunaModelConfig, description="Default model configuration"
    )

    elasticsearch_url: str = Field(
        default="http://localhost:9200", description="URL for Elasticsearch server"
    )

    show_agent_thinking: bool = Field(
        default=True, description="Whether to display agents' thinking processes"
    )

    logs_path: str = Field(default="logs", description="Path for application logs")

    persona: str = Field(default="luna", description="Which persona config to load")

    # PydanticAI specific settings
    instrumentation: bool = Field(
        default=False, description="Whether to enable OpenTelemetry instrumentation"
    )

    usage_tracking: bool = Field(
        default=True, description="Whether to track token usage and API calls"
    )

    usage_limits: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional limits on token usage"
    )
