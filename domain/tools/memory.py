"""
Memory-related tools for storing and retrieving memories from Luna's memory store.
This file contains the general-purpose memory read tool that can work with any memory type,
as well as administrative tools for manually recording memories.
Specialized tools for specific memory types are in separate modules.
"""

import traceback
from typing import Any, Dict, List, Optional

from domain.models.emotion import EmotionalState
from domain.models.enums import WorkingMemoryType
from domain.models.memory import (
    EmotionalMemory,
    EpisodicMemory,
    Memory,
    MemoryQuery,
    MemoryResult,
    RelationshipMemory,
    SemanticMemory,
    WorkingMemory,
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


class WorkingMemoryWriteTool(Tool):
    """Tool for creating memories in Luna's working memory using the memory service."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        super().__init__(
            name="add_working_memory",
            description="""Adds a working memory that will be persistently available in the system prompt.

This tool allows for a short-term memory to be added to Luna's working memory. It is
useful for preserving information that is relevant to this conversation but doesn't
deserve to be permanently remembered in Luna's long-term memory.

Working Memory Types:
- fact: Temporary factual information useful for the current conversation
- event: Minor events that don't warrant a long-term memory
- insight: Realizations or connections made during conversation
- goal: Temporary objectives or intentions for the current conversation
- emotion: Current emotional states or reactions
- thought: Key reasoning chains or inner monologue elements

When To Use:
- To preserve aspects of inner thinking and inner monologue, which are not otherwise
preserved between conversation turns
- To remember temporary or contextual information such as goals, ideas, and facts that
are mostly or entirely relevant to this conversation only
- To maintain Luna's inner world and thoughts in a coherent and consistent way

The importance value determines how many conversation turns this memory will persist
(default: 5). Higher importance (up to 10) means the memory will last longer.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the working memory",
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of working memory",
                        "enum": [mem_type.value for mem_type in WorkingMemoryType],
                    },
                    "importance": {
                        "type": "integer",
                        "description": "How many conversation turns this should persist in the working memory",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": ["content", "type"],
            },
            handler=self.handle,
            category=ToolCategory.MEMORY,
        )
        self.memory_service = memory_service

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            new_working_memory = WorkingMemory(
                type=WorkingMemoryType(tool_input.get("type")),
                content=tool_input.get("content"),
                importance=tool_input.get("importance"),
            )
            self.memory_service.add_working_memory(new_working_memory)
            return {
                "success": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class WorkingMemoryUpdateTool(Tool):
    """Tool for updating memories in Luna's working memory using the memory service."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        super().__init__(
            name="refresh_working_memory",
            description="""Refresh working memory importance to make the memory last longer

This tool lets you set the importance on a working memory to let it persist
for a longer period of time. Typically, the importance decays are a rate of
1 per conversation turn.""",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The working memory id",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "How many conversation turns this should persist in the working memory",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["id", "importance"],
            },
            handler=self.handle,
            category=ToolCategory.MEMORY,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.memory_service.refresh_working_memory(
                tool_input.get("id"), tool_input.get("importance")
            )
            return {
                "success": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
