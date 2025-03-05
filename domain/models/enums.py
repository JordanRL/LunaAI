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
    INSPECT_INTENTION = "inspect_intention"
    PERSONA_EVOLUTION = "persona_evolution"
    SUMMARIZER = "summarizer"
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
