from enum import Enum
from typing import List


# We're keeping the Enum implementation the same, but could use StrEnum if desired
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
    DEVELOPMENT_TEST = "development_test"

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
        exclude = ["dispatcher", "outputter", "persona_evolution", "development_test"]
        return [agent.value for agent in cls if agent.value not in exclude]


# ContentType enum is expanded to support more provider-specific content types
class ContentType(Enum):
    """Types of content in a message."""

    # Basic content types (common across providers)
    TEXT = "text"
    IMAGE = "image"

    # Tool-related content types
    TOOL_CALL = "tool_use"
    TOOL_RESULT = "tool_result"

    # Other types
    THINKING = "thinking"
