"""
Memory-related tools for storing and retrieving memories from Luna's memory store.
This file contains the general-purpose memory read tool that can work with any memory type,
as well as administrative tools for manually recording memories.
Specialized tools for specific memory types are in separate modules.
"""

import traceback
from typing import Any, Dict, List, Optional

from domain.models.emotion import EmotionalState
from domain.models.memory import (
    EmotionalMemory,
    EpisodicMemory,
    Memory,
    MemoryQuery,
    MemoryResult,
    RelationshipMemory,
    SemanticMemory,
)
from domain.models.tool import Tool, ToolCategory
from services.memory_service import MemoryService


class MemoryReadTool(Tool):
    """Tool for retrieving memories from Luna's memory store using the memory service."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the memory read tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="read_memory",
            description="""Retrieve memories from Luna's memory store based on a search query.

This tool searches Luna's memory for information about the user, past conversations,
and learned facts. Use this for general memory queries when you need information
but don't need to use the specialized memory type tools.

Memory types available:
- episodic: Event-based memories (conversations, interactions)
- semantic: Factual knowledge about the user or world
- emotional: Luna's emotional responses and feelings
- relationship: Information about Luna's relationship with the user
- all: All memories, regardless of type (default)

Query effectively by:
- Providing specific search terms related to what you're looking for
- Setting an importance threshold to only get significant memories
- Using keywords to find topically related memories
- Setting a reasonable limit to control how many results you get""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories",
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory to retrieve",
                        "enum": ["episodic", "semantic", "emotional", "relationship", "all"],
                        "default": "all",
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
        Process a memory retrieval request.

        Args:
            tool_input: Dictionary containing query parameters

        Returns:
            Dictionary containing retrieved memories and metadata
        """
        try:
            # Extract parameters from tool input
            query_text = tool_input.get("query", "")
            memory_type = tool_input.get("memory_type", "all")
            limit = tool_input.get("limit", 5)
            importance_threshold = tool_input.get("importance_threshold")
            user_id = tool_input.get("user_id")
            keywords = tool_input.get("keywords")

            # Check if memory service is available
            if not self.memory_service:
                return {
                    "memories": [],
                    "query": query_text,
                    "total_found": 0,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                }

            # Create a query object
            query = MemoryQuery(
                query=query_text,
                memory_type=memory_type if memory_type != "all" else None,
                limit=limit,
                importance_threshold=importance_threshold,
                user_id=user_id,
                keywords=keywords,
            )

            # Execute the query using memory service
            result = self.memory_service.retrieve_memories(query)

            # Format memories for response
            memories_list = []
            for memory in result.memories:
                memory_dict = {
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "timestamp": (
                        memory.timestamp.isoformat()
                        if hasattr(memory.timestamp, "isoformat")
                        else memory.timestamp
                    ),
                    "keywords": memory.keywords,
                }

                # Add type-specific fields
                if memory.memory_type == "episodic" and isinstance(memory, EpisodicMemory):
                    memory_dict["participants"] = memory.participants
                    memory_dict["context"] = memory.context

                elif memory.memory_type == "semantic" and isinstance(memory, SemanticMemory):
                    memory_dict["certainty"] = memory.certainty
                    memory_dict["source"] = memory.source
                    memory_dict["domain"] = memory.domain

                elif memory.memory_type == "emotional" and isinstance(memory, EmotionalMemory):
                    memory_dict["trigger"] = memory.trigger
                    if memory.emotion:
                        memory_dict["emotion"] = {
                            "pleasure": memory.emotion.pleasure,
                            "arousal": memory.emotion.arousal,
                            "dominance": memory.emotion.dominance,
                        }

                elif memory.memory_type == "relationship" and isinstance(
                    memory, RelationshipMemory
                ):
                    memory_dict["relationship_type"] = memory.relationship_type
                    memory_dict["closeness"] = memory.closeness
                    memory_dict["trust"] = memory.trust

                memories_list.append(memory_dict)

            # Return the result
            response = {
                "memories": memories_list,
                "query": query_text,
                "total_found": result.total_found,
                "memory_type": memory_type,
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
