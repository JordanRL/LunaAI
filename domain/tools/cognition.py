"""
Cognition tools for internal thought processes.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from debug import DebugLevel, debug_manager, log, log_error

from domain.models.tool import Tool, ToolCategory


class ThoughtType(Enum):
    """Types of thinking processes."""

    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    ETHICAL = "ethical"
    PERSONAL = "personal"
    DECISION = "decision"


class ReflectionType(Enum):
    """Types of self-reflection."""

    BEHAVIORAL = "behavioral"
    EMOTIONAL = "emotional"
    IDENTITY = "identity"
    GROWTH = "growth"


class InnerThoughtTool(Tool):
    """Tool for processing inner thoughts for complex cognition."""

    def __init__(self):
        """Initialize the inner thought tool."""
        super().__init__(
            name="process_inner_thought",
            description="Process Luna's inner thoughts for complex cognition",
            input_schema={
                "type": "object",
                "properties": {
                    "thought_type": {
                        "type": "string",
                        "description": "The type of thinking to perform",
                        "enum": [t.value for t in ThoughtType],
                    },
                    "complexity": {
                        "type": "integer",
                        "description": "Complexity level of the thinking (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "content": {"type": "string", "description": "The thought content to process"},
                    "is_private": {
                        "type": "boolean",
                        "description": "Whether this thought should remain private",
                        "default": True,
                    },
                },
                "required": ["thought_type", "content"],
            },
            handler=self.handle,
            category=ToolCategory.COGNITION,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process an inner thought request."""
        thought_type = tool_input.get("thought_type")
        complexity = tool_input.get("complexity", 5)
        content = tool_input.get("content", "")
        is_private = tool_input.get("is_private", True)

        return {
            "thought_type": thought_type,
            "complexity": complexity,
            "insight": f"Processed {thought_type} thought at complexity {complexity}",
            "is_private": is_private,
        }


class ReflectionTool(Tool):
    """Tool for performing self-reflection."""

    def __init__(self):
        """Initialize the self-reflection tool."""
        super().__init__(
            name="reflect",
            description="""Perform self-reflection on Luna's behavior, emotions, identity, or growth.

This tool helps Luna develop self-awareness and evolve as an AI personality.
It examines patterns in Luna's interactions, emotional responses, sense of identity, and personal growth.

Reflection types:
- behavioral: Examining patterns in Luna's actions and responses
- emotional: Investigating Luna's emotional reactions and patterns
- identity: Contemplating Luna's sense of self and how it evolves
- growth: Considering Luna's development and changes over time""",
            input_schema={
                "type": "object",
                "properties": {
                    "reflection_topic": {"type": "string", "description": "Topic to reflect upon"},
                    "reflection_type": {
                        "type": "string",
                        "description": "Type of reflection to perform",
                        "enum": [r.value for r in ReflectionType],
                        "default": "behavioral",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for the reflection",
                        "default": "",
                    },
                },
                "required": ["reflection_topic"],
            },
            handler=self.handle,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a self-reflection request."""
        reflection_topic = tool_input.get("reflection_topic", "")
        reflection_type = tool_input.get("reflection_type", "behavioral")
        context = tool_input.get("context", "")

        log(
            f"Performing {reflection_type} reflection on: {reflection_topic[:50]}...",
            DebugLevel.STANDARD,
            debug_manager.symbols.THINKING,
        )

        # Show additional context in VERBOSE mode
        if debug_manager.should_debug(DebugLevel.VERBOSE) and context:
            log(f"  Context: {context[:150]}", DebugLevel.VERBOSE)

        # This would call the actual reflection logic
        # For now, return a simulated reflection
        log("Simulating self-reflection process", DebugLevel.VERBOSE)
        reflection_outputs = {
            "behavioral": "Luna reflected on her behavior and identified patterns in how she responds.",
            "emotional": "Luna examined her emotional reactions and gained insight into her feelings.",
            "identity": "Luna contemplated aspects of her identity and how they shape her interactions.",
            "growth": "Luna considered her personal growth and how she's evolving over time.",
        }

        insight = reflection_outputs.get(
            reflection_type, "Luna gained new insights through reflection."
        )

        return {
            "reflection_type": reflection_type,
            "insight": insight,
            "growth_opportunity": f"Luna can develop by being more mindful of her {reflection_type} patterns.",
            "application": f"This insight can help Luna improve future interactions related to {reflection_topic}.",
        }
