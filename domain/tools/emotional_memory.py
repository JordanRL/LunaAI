"""
Specialized tools for working with emotional memories in Luna's memory system.
"""

import traceback
from typing import Any, Dict, List, Optional

from domain.models.emotion import EmotionalState
from domain.models.memory import EmotionalMemory, EmotionalMemoryQuery, MemoryResult
from domain.models.tool import Tool, ToolCategory
from services.memory_service import MemoryService


class EmotionalMemoryReadTool(Tool):
    """Tool for retrieving emotional memories from Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the emotional memory read tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="read_emotional_memory",
            description="""Retrieve emotional memories from Luna's memory store based on a search query.

Emotional memories represent Luna's emotional responses, feelings, and reactions to events.
Use this tool when you need to recall Luna's emotional experiences, reactions, and feelings.

This specialized tool provides additional filtering options specific to emotional memories:
- Filter by emotional trigger
- Filter by emotional response in the PAD (pleasure-arousal-dominance) model
- Filter by emotional intensity

Query effectively by:
- Providing specific search terms related to the emotional experience
- Filtering by trigger to find memories related to specific stimuli
- Using emotional thresholds to find memories with specific emotional characteristics""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant emotional memories",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to retrieve",
                        "default": 5,
                    },
                    "importance_threshold": {
                        "type": "integer",
                        "description": "Minimum importance level (1-10) of memories to retrieve",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The user ID to retrieve memories for",
                    },
                    "trigger": {
                        "type": "string",
                        "description": "Filter by the trigger that caused this emotional response",
                    },
                    "event_pleasure_threshold": {
                        "type": "number",
                        "description": "Minimum pleasure level (-1.0 to 1.0) of the event",
                        "minimum": -1.0,
                        "maximum": 1.0,
                    },
                    "event_arousal_threshold": {
                        "type": "number",
                        "description": "Minimum arousal level (-1.0 to 1.0) of the event",
                        "minimum": -1.0,
                        "maximum": 1.0,
                    },
                    "event_dominance_threshold": {
                        "type": "number",
                        "description": "Minimum dominance level (-1.0 to 1.0) of the event",
                        "minimum": -1.0,
                        "maximum": 1.0,
                    },
                    "keywords": {
                        "type": "array",
                        "description": "Keywords to search for in the memories",
                        "items": {"type": "string"},
                    },
                },
                "required": ["query"],
            },
            handler=self.handle,
            category=ToolCategory.MEMORY,
        )
        self.memory_service = memory_service

    def set_memory_service(self, memory_service: MemoryService) -> None:
        """
        Set the memory service after initialization.

        Args:
            memory_service: Service for memory operations
        """
        self.memory_service = memory_service

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an emotional memory retrieval request.

        Args:
            tool_input: Dictionary containing query parameters

        Returns:
            Dictionary containing retrieved emotional memories and metadata
        """
        try:
            # Extract parameters from tool input
            query_text = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            importance_threshold = tool_input.get("importance_threshold")
            user_id = tool_input.get("user_id")
            trigger = tool_input.get("trigger")
            event_pleasure_threshold = tool_input.get("event_pleasure_threshold")
            event_arousal_threshold = tool_input.get("event_arousal_threshold")
            event_dominance_threshold = tool_input.get("event_dominance_threshold")
            keywords = tool_input.get("keywords")

            # Check if memory service is available
            if not self.memory_service:
                return {
                    "memories": [],
                    "query": query_text,
                    "total_found": 0,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                }

            # Create a specialized emotional memory query
            query = EmotionalMemoryQuery(
                query=query_text,
                limit=limit,
                importance_threshold=importance_threshold,
                user_id=user_id,
                keywords=keywords,
                trigger=trigger,
                event_pleasure_threshold=event_pleasure_threshold,
                event_arousal_threshold=event_arousal_threshold,
                event_dominance_threshold=event_dominance_threshold,
            )

            # Execute the query using memory service
            result = self.memory_service.retrieve_memories(query)

            # Format memories for response
            memories_list = []
            for memory in result.memories:
                if not isinstance(memory, EmotionalMemory):
                    continue  # Skip non-emotional memories if any

                memory_dict = {
                    "id": memory.id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "timestamp": (
                        memory.timestamp.isoformat()
                        if hasattr(memory.timestamp, "isoformat")
                        else memory.timestamp
                    ),
                    "keywords": memory.keywords,
                    "trigger": memory.trigger,
                    "event_pleasure": memory.event_pleasure,
                    "event_arousal": memory.event_arousal,
                    "event_dominance": memory.event_dominance,
                }

                # Add emotional context if it exists
                if memory.emotion:
                    memory_dict["emotion"] = {
                        "pleasure": memory.emotion.pleasure,
                        "arousal": memory.emotion.arousal,
                        "dominance": memory.emotion.dominance,
                    }

                memories_list.append(memory_dict)

            # Return the result
            response = {
                "memories": memories_list,
                "query": query_text,
                "total_found": len(memories_list),
            }

            if result.message:
                response["message"] = result.message

            return response

        except Exception as e:
            error_msg = f"Error retrieving emotional memories: {str(e)}"

            # Return empty result on error
            return {
                "memories": [],
                "query": tool_input.get("query", ""),
                "total_found": 0,
                "error": str(e),
            }


class EmotionalMemoryWriteTool(Tool):
    """Tool for creating emotional memories in Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the emotional memory write tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="write_emotional_memory",
            description="""Create a new emotional memory in Luna's memory store.

Emotional memories represent Luna's emotional responses, feelings, and reactions to events.
Use this tool to record important emotional experiences that Luna should remember.

This specialized tool provides additional parameters specific to emotional memories:
- Record the trigger that caused this emotional response
- Capture the emotional reaction using the PAD (pleasure-arousal-dominance) model
- Document the intensity of the emotional response

The memory will be stored in Luna's long-term memory for future recall and retrieval.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The emotional memory content to store",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance rating from 1 to 10",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                    "trigger": {
                        "type": "string",
                        "description": "What triggered this emotional response",
                        "default": "",
                    },
                    "event_pleasure": {
                        "type": "number",
                        "description": "Pleasure dimension of the event (-1.0 to 1.0)",
                        "minimum": -1.0,
                        "maximum": 1.0,
                        "default": 0.0,
                    },
                    "event_arousal": {
                        "type": "number",
                        "description": "Arousal dimension of the event (-1.0 to 1.0)",
                        "minimum": -1.0,
                        "maximum": 1.0,
                        "default": 0.0,
                    },
                    "event_dominance": {
                        "type": "number",
                        "description": "Dominance dimension of the event (-1.0 to 1.0)",
                        "minimum": -1.0,
                        "maximum": 1.0,
                        "default": 0.0,
                    },
                    "emotion": {
                        "type": "object",
                        "description": "Luna's emotional response (PAD model)",
                        "properties": {
                            "pleasure": {
                                "type": "number",
                                "description": "Pleasure dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0,
                            },
                            "arousal": {
                                "type": "number",
                                "description": "Arousal dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0,
                            },
                            "dominance": {
                                "type": "number",
                                "description": "Dominance dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0,
                            },
                        },
                    },
                    "keywords": {
                        "type": "array",
                        "description": "Keywords to associate with this memory for better retrieval",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The user ID this memory is associated with",
                    },
                },
                "required": ["content"],
            },
            handler=self.handle,
            category=ToolCategory.MEMORY,
        )
        self.memory_service = memory_service

    def set_memory_service(self, memory_service: MemoryService) -> None:
        """
        Set the memory service after initialization.

        Args:
            memory_service: Service for memory operations
        """
        self.memory_service = memory_service

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an emotional memory creation request.

        Args:
            tool_input: Dictionary containing memory data

        Returns:
            Dictionary containing operation result and metadata
        """
        try:
            content = tool_input.get("content", "")
            importance = tool_input.get("importance", 5)
            trigger = tool_input.get("trigger", "")
            event_pleasure = tool_input.get("event_pleasure", 0.0)
            event_arousal = tool_input.get("event_arousal", 0.0)
            event_dominance = tool_input.get("event_dominance", 0.0)
            keywords = tool_input.get("keywords", [])
            user_id = tool_input.get("user_id")

            # Check if memory service is available
            if not self.memory_service:
                return {
                    "success": False,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                    "message": "Failed to store emotional memory: Memory service unavailable",
                }

            # Create emotional state if provided
            emotion = None
            if "emotion" in tool_input and tool_input["emotion"]:
                emotion_data = tool_input["emotion"]
                emotion = EmotionalState(
                    pleasure=emotion_data.get("pleasure"),
                    arousal=emotion_data.get("arousal"),
                    dominance=emotion_data.get("dominance"),
                )

            # Create new emotional memory
            memory = EmotionalMemory(
                content=content,
                importance=importance,
                trigger=trigger,
                event_pleasure=event_pleasure,
                event_arousal=event_arousal,
                event_dominance=event_dominance,
                keywords=keywords,
                user_id=user_id,
                emotion=emotion,
            )

            # Store the memory
            memory_id = self.memory_service.store_memory(memory)

            if memory_id:
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "memory_type": "emotional",
                    "importance": importance,
                    "message": f"Successfully stored emotional memory with ID {memory_id}",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store memory",
                    "message": "Failed to store emotional memory",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create emotional memory: {str(e)}",
            }
