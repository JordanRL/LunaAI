"""
Specialized tools for working with relationship memories in Luna's memory system.
"""

import traceback
from typing import Any, Dict, List, Optional

from debug import DebugLevel, debug_manager, log, log_error

from domain.models.emotion import EmotionalState
from domain.models.memory import MemoryResult, RelationshipMemory, RelationshipMemoryQuery
from domain.models.tool import Tool, ToolCategory
from services.memory_service import MemoryService


class RelationshipMemoryReadTool(Tool):
    """Tool for retrieving relationship memories from Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the relationship memory read tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="read_relationship_memory",
            description="""Retrieve relationship memories from Luna's memory store based on a search query.

Relationship memories represent Luna's understanding of her relationships with users and others.
Use this tool when you need to recall information about relationships, dynamics, and connections.

This specialized tool provides additional filtering options specific to relationship memories:
- Filter by relationship type
- Filter by closeness, trust, and apprehension levels
- Filter by shared experiences and connection points
- Filter by inside references

Query effectively by:
- Providing specific search terms related to the relationship
- Filtering by relationship type to find specific kinds of connections
- Using thresholds for relationship qualities (closeness, trust, etc.)""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant relationship memories",
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
                    "relationship_type": {
                        "type": "string",
                        "description": "Filter by the type of relationship",
                    },
                    "closeness_threshold": {
                        "type": "number",
                        "description": "Minimum closeness level (0.0-1.0) of the relationship",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "trust_threshold": {
                        "type": "number",
                        "description": "Minimum trust level (0.0-1.0) of the relationship",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "apprehension_threshold": {
                        "type": "number",
                        "description": "Minimum apprehension level (0.0-1.0) of the relationship",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "shared_experiences": {
                        "type": "array",
                        "description": "Filter by shared experiences in the relationship",
                        "items": {"type": "string"},
                    },
                    "connection_points": {
                        "type": "array",
                        "description": "Filter by connection points in the relationship",
                        "items": {"type": "string"},
                    },
                    "inside_references": {
                        "type": "array",
                        "description": "Filter by inside references in the relationship",
                        "items": {"type": "string"},
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
        Process a relationship memory retrieval request.

        Args:
            tool_input: Dictionary containing query parameters

        Returns:
            Dictionary containing retrieved relationship memories and metadata
        """
        try:
            # Extract parameters from tool input
            query_text = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            importance_threshold = tool_input.get("importance_threshold")
            user_id = tool_input.get("user_id")
            relationship_type = tool_input.get("relationship_type")
            closeness_threshold = tool_input.get("closeness_threshold")
            trust_threshold = tool_input.get("trust_threshold")
            apprehension_threshold = tool_input.get("apprehension_threshold")
            shared_experiences = tool_input.get("shared_experiences")
            connection_points = tool_input.get("connection_points")
            inside_references = tool_input.get("inside_references")
            keywords = tool_input.get("keywords")

            log(
                f"Relationship memory query: '{query_text}' | Limit: {limit}",
                DebugLevel.STANDARD,
                debug_manager.symbols.MEMORY,
            )

            # Check if memory service is available
            if not self.memory_service:
                log_error("Memory service is not available", "relationship_memory_tool")
                return {
                    "memories": [],
                    "query": query_text,
                    "total_found": 0,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                }

            # Log additional details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                filter_details = []
                if user_id:
                    filter_details.append(f"user_id: {user_id}")
                if importance_threshold:
                    filter_details.append(f"importance: ≥{importance_threshold}")
                if relationship_type:
                    filter_details.append(f"relationship_type: {relationship_type}")
                if closeness_threshold:
                    filter_details.append(f"closeness: ≥{closeness_threshold}")
                if trust_threshold:
                    filter_details.append(f"trust: ≥{trust_threshold}")
                if apprehension_threshold:
                    filter_details.append(f"apprehension: ≥{apprehension_threshold}")
                if shared_experiences:
                    filter_details.append(f"shared_experiences: [{', '.join(shared_experiences)}]")
                if connection_points:
                    filter_details.append(f"connection_points: [{', '.join(connection_points)}]")
                if inside_references:
                    filter_details.append(f"inside_references: [{', '.join(inside_references)}]")
                if keywords:
                    filter_details.append(f"keywords: [{', '.join(keywords)}]")

                if filter_details:
                    log(f"  Filters: {', '.join(filter_details)}", DebugLevel.VERBOSE)

            # Create a specialized relationship memory query
            query = RelationshipMemoryQuery(
                query=query_text,
                limit=limit,
                importance_threshold=importance_threshold,
                user_id=user_id,
                keywords=keywords,
                relationship_type=relationship_type,
                closeness_threshold=closeness_threshold,
                trust_threshold=trust_threshold,
                apprehension_threshold=apprehension_threshold,
                shared_experiences=shared_experiences,
                connection_points=connection_points,
                inside_references=inside_references,
            )

            # Execute the query using memory service
            result = self.memory_service.retrieve_memories(query)

            # Process the query results
            memory_count = len(result.memories)
            log(
                f"Found {memory_count} relationship memories matching '{query_text}'",
                DebugLevel.STANDARD,
                debug_manager.symbols.SUCCESS,
            )

            # Format memories for response
            memories_list = []
            for memory in result.memories:
                if not isinstance(memory, RelationshipMemory):
                    continue  # Skip non-relationship memories if any

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
                    "relationship_type": memory.relationship_type,
                    "closeness": memory.closeness,
                    "trust": memory.trust,
                    "apprehension": memory.apprehension,
                    "shared_experiences": memory.shared_experiences,
                    "connection_points": memory.connection_points,
                    "inside_references": memory.inside_references,
                }

                # Add emotional context if it exists
                if memory.emotion:
                    memory_dict["emotion"] = {
                        "pleasure": memory.emotion.pleasure,
                        "arousal": memory.emotion.arousal,
                        "dominance": memory.emotion.dominance,
                    }

                memories_list.append(memory_dict)

            # Show memory previews in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE) and memories_list:
                log("Relationship memory results:", DebugLevel.VERBOSE)
                for i, memory in enumerate(memories_list[:3]):  # Show up to 3 memories
                    content_preview = debug_manager.truncate_content(memory.get("content", ""), 120)
                    importance = memory.get("importance", 5)
                    rel_type = memory.get("relationship_type", "")
                    closeness = memory.get("closeness", 0.5)
                    trust = memory.get("trust", 0.5)
                    if rel_type:
                        rel_text = (
                            f" (type: {rel_type}, closeness: {closeness:.1f}, trust: {trust:.1f})"
                        )
                    else:
                        rel_text = ""
                    log(
                        f"  {i+1}. [relationship] {content_preview} (importance: {importance}){rel_text}",
                        DebugLevel.VERBOSE,
                    )

                if len(memories_list) > 3:
                    log(f"  ... and {len(memories_list) - 3} more", DebugLevel.VERBOSE)

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
            error_msg = f"Error retrieving relationship memories: {str(e)}"
            log_error(error_msg, "relationship_memory_retrieval")

            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)

            # Return empty result on error
            return {
                "memories": [],
                "query": tool_input.get("query", ""),
                "total_found": 0,
                "error": str(e),
            }


class RelationshipMemoryWriteTool(Tool):
    """Tool for creating relationship memories in Luna's memory store."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the relationship memory write tool with access to the memory service.

        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="write_relationship_memory",
            description="""Create a new relationship memory in Luna's memory store.

Relationship memories represent Luna's understanding of her relationships with users and others.
Use this tool to record important relationship information that Luna should remember.

This specialized tool provides additional parameters specific to relationship memories:
- Record the type of relationship
- Track closeness, trust, and apprehension levels
- Document shared experiences and connection points
- Store inside references and relationship-specific context

The memory will be stored in Luna's long-term memory for future recall and retrieval.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The relationship memory content to store",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance rating from 1 to 10",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "The type of relationship (e.g., 'friendship', 'professional')",
                        "default": "",
                    },
                    "closeness": {
                        "type": "number",
                        "description": "Level of closeness in the relationship (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5,
                    },
                    "trust": {
                        "type": "number",
                        "description": "Level of trust in the relationship (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5,
                    },
                    "apprehension": {
                        "type": "number",
                        "description": "Level of apprehension in the relationship (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5,
                    },
                    "shared_experiences": {
                        "type": "array",
                        "description": "Shared experiences in this relationship",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "connection_points": {
                        "type": "array",
                        "description": "Connection points in this relationship",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "inside_references": {
                        "type": "array",
                        "description": "Inside references in this relationship",
                        "items": {"type": "string"},
                        "default": [],
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
        Process a relationship memory creation request.

        Args:
            tool_input: Dictionary containing memory data

        Returns:
            Dictionary containing operation result and metadata
        """
        try:
            content = tool_input.get("content", "")
            importance = tool_input.get("importance", 5)
            relationship_type = tool_input.get("relationship_type", "")
            closeness = tool_input.get("closeness", 0.5)
            trust = tool_input.get("trust", 0.5)
            apprehension = tool_input.get("apprehension", 0.5)
            shared_experiences = tool_input.get("shared_experiences", [])
            connection_points = tool_input.get("connection_points", [])
            inside_references = tool_input.get("inside_references", [])
            keywords = tool_input.get("keywords", [])
            user_id = tool_input.get("user_id")

            # Check if memory service is available
            if not self.memory_service:
                log_error("Memory service is not available", "relationship_memory_tool")
                return {
                    "success": False,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                    "message": "Failed to store relationship memory: Memory service unavailable",
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

            # Create new relationship memory
            memory = RelationshipMemory(
                content=content,
                importance=importance,
                relationship_type=relationship_type,
                closeness=closeness,
                trust=trust,
                apprehension=apprehension,
                shared_experiences=shared_experiences,
                connection_points=connection_points,
                inside_references=inside_references,
                keywords=keywords,
                user_id=user_id,
                emotion=emotion,
            )

            # Store the memory
            memory_id = self.memory_service.store_memory(memory)

            if memory_id:
                log(
                    f"Created relationship memory: '{content[:50]}...' | Importance: {importance}/10",
                    DebugLevel.STANDARD,
                    debug_manager.symbols.MEMORY,
                )

                # Show more details in VERBOSE mode
                if debug_manager.should_debug(DebugLevel.VERBOSE):
                    details = []
                    if relationship_type:
                        details.append(f"Type: {relationship_type}")
                    details.append(f"Closeness: {closeness:.2f}, Trust: {trust:.2f}")
                    if shared_experiences:
                        details.append(f"Shared experiences: [{', '.join(shared_experiences[:3])}]")
                        if len(shared_experiences) > 3:
                            details[-1] += f" and {len(shared_experiences) - 3} more"
                    if connection_points:
                        details.append(f"Connection points: [{', '.join(connection_points[:3])}]")
                        if len(connection_points) > 3:
                            details[-1] += f" and {len(connection_points) - 3} more"
                    if keywords:
                        details.append(f"Keywords: [{', '.join(keywords)}]")
                    if emotion:
                        pad_values = []
                        if emotion.pleasure is not None:
                            pad_values.append(f"P:{emotion.pleasure:.2f}")
                        if emotion.arousal is not None:
                            pad_values.append(f"A:{emotion.arousal:.2f}")
                        if emotion.dominance is not None:
                            pad_values.append(f"D:{emotion.dominance:.2f}")
                        if pad_values:
                            details.append(f"Emotion: {' '.join(pad_values)}")

                    if details:
                        log("  Details: " + " | ".join(details), DebugLevel.VERBOSE)

                return {
                    "success": True,
                    "memory_id": memory_id,
                    "memory_type": "relationship",
                    "importance": importance,
                    "message": f"Successfully stored relationship memory with ID {memory_id}",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store memory",
                    "message": "Failed to store relationship memory",
                }

        except Exception as e:
            error_msg = f"Error writing relationship memory: {str(e)}"
            log_error(error_msg, "relationship_memory_storage")

            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)

            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create relationship memory: {str(e)}",
            }
