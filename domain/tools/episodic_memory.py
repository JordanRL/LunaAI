"""
Specialized tools for working with episodic memories in Luna's memory system.
"""

import traceback
from typing import Any, Dict, List, Optional

from domain.models.emotion import EmotionalState
from domain.models.memory import EpisodicMemory, EpisodicMemoryQuery, MemoryResult
from domain.models.tool import Tool, ToolCategory
from services.memory_service import MemoryService


class EpisodicMemoryReadTool(Tool):
    """Tool for retrieving episodic memories from Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the episodic memory read tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="read_episodic_memory",
            description="""Retrieve episodic memories from Luna's memory store based on a search query.

Episodic memories represent Luna's event-based memories of conversations and interactions.
Use this tool when you need to recall specific events, conversations, or interactions with users.

This specialized tool provides additional filtering options specific to episodic memories:
- Filter by participants involved in the memory
- Filter by contextual setting of the memory

Query effectively by:
- Providing specific search terms related to the conversation or event
- Filtering by participants to find interactions with specific people
- Using the context parameter to find memories in specific settings or situations""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant episodic memories",
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
                    "participants": {
                        "type": "array",
                        "description": "Filter by people involved in the memory",
                        "items": {"type": "string"},
                    },
                    "context": {
                        "type": "string",
                        "description": "Filter by the setting or context of the memory",
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
        Process an episodic memory retrieval request.

        Args:
            tool_input: Dictionary containing query parameters

        Returns:
            Dictionary containing retrieved episodic memories and metadata
        """
        try:
            # Extract parameters from tool input
            query_text = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            importance_threshold = tool_input.get("importance_threshold")
            user_id = tool_input.get("user_id")
            participants = tool_input.get("participants")
            context = tool_input.get("context")
            keywords = tool_input.get("keywords")

            # Check if memory service is available
            if not self.memory_service:
                return {
                    "memories": [],
                    "query": query_text,
                    "total_found": 0,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                }

            # Create a specialized episodic memory query
            query = EpisodicMemoryQuery(
                query=query_text,
                limit=limit,
                importance_threshold=importance_threshold,
                user_id=user_id,
                keywords=keywords,
                participants=participants,
                context=context,
            )

            # Execute the query using memory service
            result = self.memory_service.retrieve_memories(query)

            # Format memories for response
            memories_list = []
            for memory in result.memories:
                if not isinstance(memory, EpisodicMemory):
                    continue  # Skip non-episodic memories if any

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
                    "participants": memory.participants,
                    "context": memory.context,
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
            # Return empty result on error
            return {
                "memories": [],
                "query": tool_input.get("query", ""),
                "total_found": 0,
                "error": str(e),
            }


class EpisodicMemoryWriteTool(Tool):
    """Tool for creating episodic memories in Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the episodic memory write tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="write_episodic_memory",
            description="""Create a new episodic memory in Luna's memory store.

Episodic memories represent Luna's event-based memories of conversations and interactions.
Use this tool to record important events, conversations, and interactions that Luna should remember.

This specialized tool provides additional parameters specific to episodic memories:
- Record participants involved in the memory
- Capture the context or setting of the memory
- Store emotional context associated with the memory

The memory will be stored in Luna's long-term memory for future recall and retrieval.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The episodic memory content to store",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance rating from 1 to 10",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                    "participants": {
                        "type": "array",
                        "description": "People involved in this memory",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "context": {
                        "type": "string",
                        "description": "The setting or situation where this memory occurred",
                        "default": "",
                    },
                    "emotion": {
                        "type": "object",
                        "description": "Emotional context associated with this memory (PAD model)",
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
        Process an episodic memory creation request.

        Args:
            tool_input: Dictionary containing memory data

        Returns:
            Dictionary containing operation result and metadata
        """
        try:
            content = tool_input.get("content", "")
            importance = tool_input.get("importance", 5)
            participants = tool_input.get("participants", [])
            context = tool_input.get("context", "")
            keywords = tool_input.get("keywords", [])
            user_id = tool_input.get("user_id")

            # Check if memory service is available
            if not self.memory_service:
                return {
                    "success": False,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                    "message": "Failed to store episodic memory: Memory service unavailable",
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

            # Create new episodic memory
            memory = EpisodicMemory(
                content=content,
                importance=importance,
                participants=participants,
                context=context,
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
                    "memory_type": "episodic",
                    "importance": importance,
                    "message": f"Successfully stored episodic memory with ID {memory_id}",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store memory",
                    "message": "Failed to store episodic memory",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create episodic memory: {str(e)}",
            }
