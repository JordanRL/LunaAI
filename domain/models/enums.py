from enum import Enum
from typing import List


class WorkingMemoryType(Enum):
    """Types of working memory."""

    FACT = "fact"  # To preserve a fact that is useful for this conversation but that Luna doesn't need to remember later
    EVENT = "event"  # To preserve a minor even that doesn't warrant a long-term memory
    INSIGHT = "insight"  # To preserve an insight
    GOAL = "goal"  # To preserve a temporary goal in the current conversation
    EMOTION = "emotion"  # To preserve an emotion
    THOUGHT = "thought"  # For chain of thought preservation


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
    SUMMARIZER = "summarizer"
    SENTIMENT = "sentiment"
    INSPECT_INTENTION = "inspect_intention"
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
