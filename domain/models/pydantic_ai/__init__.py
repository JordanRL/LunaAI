"""
PydanticAI integration for Luna.

This module provides components for integrating PydanticAI into
Luna's architecture, enabling provider-agnostic AI interactions,
structured outputs, and advanced features.

Key components:
- Adapter: Convert between domain models and PydanticAI models
- Config: Configuration models for PydanticAI integration
- Example: Reference implementations
"""

from domain.models.pydantic_ai.adapter import PAIAdapter, legacy_tool_to_pai_function
from domain.models.pydantic_ai.config import (
    LunaAgentConfig,
    LunaAppConfig,
    LunaModelConfig,
    ProviderType,
)
