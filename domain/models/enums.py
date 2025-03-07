from enum import Enum
from typing import List


class AgentType(Enum):
    """
    Available agent types for routing.
    """
    DISPATCHER = "dispatcher"
    MEMORY_RETRIEVER = "memory_retriever"
    MEMORY_WRITER = "memory_writer"
    EMOTION_PROCESSOR = "emotion_processor"
    RELATIONSHIP_MANAGER = "relationship_manager"
    INNER_THOUGHT = "inner_thought"
    PERSONA_EVOLUTION = "persona_evolution"
    SELF_REFLECTION = "self_reflection"
    OUTPUTTER = "outputter"

    @classmethod
    def to_list(cls) -> List[str]:
        """Convert enum values to a list of strings."""
        return [agent.value for agent in cls]

    @classmethod
    def filtered_to_list(cls) -> List[str]:
        """
        Convert enum values to a list of strings, excluding some specific agents.
        This is useful for tools that should not route to certain agents.
        """
        exclude = ["dispatcher", "outputter", "persona_evolution"]
        return [agent.value for agent in cls if agent.value not in exclude]


class ContentType(Enum):
    """Types of content in a message."""
    TEXT = "text"
    TOOL_CALL = "tool_use"  # Anthropic API uses "tool_use" for tool calls
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    # Add other content types as needed
