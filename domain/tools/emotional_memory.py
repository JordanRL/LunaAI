"""
Specialized tools for working with emotional memories in Luna's memory system.
"""

import traceback
from typing import Any, Dict, List, Optional

from debug import DebugLevel, debug_manager, log, log_error

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

            log(
                f"Emotional memory query: '{query_text}' | Limit: {limit}",
                DebugLevel.STANDARD,
                debug_manager.symbols.MEMORY,
            )

            # Check if memory service is available
            if not self.memory_service:
                log_error("Memory service is not available", "emotional_memory_tool")
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
                if trigger:
                    filter_details.append(f"trigger: {trigger}")

                # Add emotional thresholds if provided
                pad_thresholds = []
                if event_pleasure_threshold is not None:
                    pad_thresholds.append(f"P:≥{event_pleasure_threshold:.2f}")
                if event_arousal_threshold is not None:
                    pad_thresholds.append(f"A:≥{event_arousal_threshold:.2f}")
                if event_dominance_threshold is not None:
                    pad_thresholds.append(f"D:≥{event_dominance_threshold:.2f}")
                if pad_thresholds:
                    filter_details.append("Emotion: " + " ".join(pad_thresholds))

                if keywords:
                    filter_details.append(f"keywords: [{', '.join(keywords)}]")

                if filter_details:
                    log(f"  Filters: {', '.join(filter_details)}", DebugLevel.VERBOSE)

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

            # Process the query results
            memory_count = len(result.memories)
            log(
                f"Found {memory_count} emotional memories matching '{query_text}'",
                DebugLevel.STANDARD,
                debug_manager.symbols.SUCCESS,
            )

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

            # Show memory previews in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE) and memories_list:
                log("Emotional memory results:", DebugLevel.VERBOSE)
                for i, memory in enumerate(memories_list[:3]):  # Show up to 3 memories
                    content_preview = debug_manager.truncate_content(memory.get("content", ""), 120)
                    importance = memory.get("importance", 5)
                    trigger = memory.get("trigger", "")
                    if trigger:
                        trigger_text = f" (trigger: {trigger})"
                    else:
                        trigger_text = ""
                    log(
                        f"  {i+1}. [emotional] {content_preview} (importance: {importance}){trigger_text}",
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
            error_msg = f"Error retrieving emotional memories: {str(e)}"
            log_error(error_msg, "emotional_memory_retrieval")

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
                log_error("Memory service is not available", "emotional_memory_tool")
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
                log(
                    f"Created emotional memory: '{content[:50]}...' | Importance: {importance}/10",
                    DebugLevel.STANDARD,
                    debug_manager.symbols.MEMORY,
                )

                # Show more details in VERBOSE mode
                if debug_manager.should_debug(DebugLevel.VERBOSE):
                    details = []
                    if trigger:
                        details.append(f"Trigger: {trigger}")

                    # Add event emotional details
                    event_pad = []
                    event_pad.append(f"P:{event_pleasure:.2f}")
                    event_pad.append(f"A:{event_arousal:.2f}")
                    event_pad.append(f"D:{event_dominance:.2f}")
                    details.append(f"Event: {' '.join(event_pad)}")

                    if keywords:
                        details.append(f"Keywords: [{', '.join(keywords)}]")

                    # Add Luna's emotional response if provided
                    if emotion:
                        pad_values = []
                        if emotion.pleasure is not None:
                            pad_values.append(f"P:{emotion.pleasure:.2f}")
                        if emotion.arousal is not None:
                            pad_values.append(f"A:{emotion.arousal:.2f}")
                        if emotion.dominance is not None:
                            pad_values.append(f"D:{emotion.dominance:.2f}")
                        if pad_values:
                            details.append(f"Luna's Emotion: {' '.join(pad_values)}")

                    if details:
                        log("  Details: " + " | ".join(details), DebugLevel.VERBOSE)

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
            error_msg = f"Error writing emotional memory: {str(e)}"
            log_error(error_msg, "emotional_memory_storage")

            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)

            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create emotional memory: {str(e)}",
            }
