"""
Specialized tools for working with semantic memories in Luna's memory system.
"""

from typing import Dict, List, Any, Optional
import traceback

from domain.models.tool import Tool, ToolCategory
from domain.models.memory import (
    SemanticMemory, SemanticMemoryQuery, MemoryResult
)
from domain.models.emotion import EmotionalState
from services.memory_service import MemoryService
from debug import debug_manager, DebugLevel, log, log_error


class SemanticMemoryReadTool(Tool):
    """Tool for retrieving semantic memories from Luna's memory store."""
    
    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the semantic memory read tool with access to the memory service.
        
        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="read_semantic_memory",
            description="""Retrieve semantic memories from Luna's memory store based on a search query.

Semantic memories represent Luna's factual knowledge about the world, users, and learned information.
Use this tool when you need to recall facts, knowledge, user preferences, or information Luna has learned.

This specialized tool provides additional filtering options specific to semantic memories:
- Filter by certainty level of the knowledge
- Filter by domain of knowledge
- Filter by source of information
- Filter by source reliability

Query effectively by:
- Providing specific search terms related to the facts or information you need
- Filtering by domain to find knowledge in specific categories
- Using certainty thresholds when you need reliable information""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant semantic memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to retrieve",
                        "default": 5
                    },
                    "importance_threshold": {
                        "type": "integer", 
                        "description": "Minimum importance level (1-10) of memories to retrieve",
                        "minimum": 1,
                        "maximum": 10
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The user ID to retrieve memories for"
                    },
                    "certainty_threshold": {
                        "type": "number",
                        "description": "Minimum certainty level (0.0-1.0) of knowledge",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "verifiability_threshold": {
                        "type": "number",
                        "description": "Minimum verifiability level (0.0-1.0) of knowledge",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "domain": {
                        "type": "string",
                        "description": "Filter by knowledge domain (e.g., 'science', 'user_preferences')"
                    },
                    "source": {
                        "type": "string",
                        "description": "Filter by source of information"
                    },
                    "source_reliability_threshold": {
                        "type": "number",
                        "description": "Minimum source reliability level (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "keywords": {
                        "type": "array",
                        "description": "Keywords to search for in the memories",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["query"]
            },
            handler=self.handle,
            category=ToolCategory.MEMORY
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
        Process a semantic memory retrieval request.
        
        Args:
            tool_input: Dictionary containing query parameters
            
        Returns:
            Dictionary containing retrieved semantic memories and metadata
        """
        try:
            # Extract parameters from tool input
            query_text = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            importance_threshold = tool_input.get("importance_threshold")
            user_id = tool_input.get("user_id")
            certainty_threshold = tool_input.get("certainty_threshold")
            verifiability_threshold = tool_input.get("verifiability_threshold")
            domain = tool_input.get("domain")
            source = tool_input.get("source")
            source_reliability_threshold = tool_input.get("source_reliability_threshold")
            keywords = tool_input.get("keywords")
            
            log(f"Semantic memory query: '{query_text}' | Limit: {limit}", 
               DebugLevel.STANDARD, debug_manager.symbols.MEMORY)
            
            # Check if memory service is available
            if not self.memory_service:
                log_error("Memory service is not available", "semantic_memory_tool")
                return {
                    "memories": [],
                    "query": query_text,
                    "total_found": 0,
                    "error": "Memory service is not available. The memory system may not be initialized yet."
                }
            
            # Log additional details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                filter_details = []
                if user_id:
                    filter_details.append(f"user_id: {user_id}")
                if importance_threshold:
                    filter_details.append(f"importance: ≥{importance_threshold}")
                if certainty_threshold:
                    filter_details.append(f"certainty: ≥{certainty_threshold}")
                if verifiability_threshold:
                    filter_details.append(f"verifiability: ≥{verifiability_threshold}")
                if domain:
                    filter_details.append(f"domain: {domain}")
                if source:
                    filter_details.append(f"source: {source}")
                if source_reliability_threshold:
                    filter_details.append(f"source_reliability: ≥{source_reliability_threshold}")
                if keywords:
                    filter_details.append(f"keywords: [{', '.join(keywords)}]")
                    
                if filter_details:
                    log(f"  Filters: {', '.join(filter_details)}", DebugLevel.VERBOSE)
            
            # Create a specialized semantic memory query
            query = SemanticMemoryQuery(
                query=query_text,
                limit=limit,
                importance_threshold=importance_threshold,
                user_id=user_id,
                keywords=keywords,
                certainty_threshold=certainty_threshold,
                verifiability_threshold=verifiability_threshold,
                domain=domain,
                source=source,
                source_reliability_threshold=source_reliability_threshold
            )
            
            # Execute the query using memory service
            result = self.memory_service.retrieve_memories(query)
            
            # Process the query results
            memory_count = len(result.memories)
            log(f"Found {memory_count} semantic memories matching '{query_text}'", 
               DebugLevel.STANDARD, debug_manager.symbols.SUCCESS)
            
            # Format memories for response
            memories_list = []
            for memory in result.memories:
                if not isinstance(memory, SemanticMemory):
                    continue  # Skip non-semantic memories if any
                
                memory_dict = {
                    "id": memory.id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat() if hasattr(memory.timestamp, 'isoformat') else memory.timestamp,
                    "keywords": memory.keywords,
                    "certainty": memory.certainty,
                    "verifiability": memory.verifiability,
                    "domain": memory.domain,
                    "source": memory.source,
                    "source_reliability": memory.source_reliability
                }
                
                # Add emotional context if it exists
                if memory.emotion:
                    memory_dict["emotion"] = {
                        "pleasure": memory.emotion.pleasure,
                        "arousal": memory.emotion.arousal,
                        "dominance": memory.emotion.dominance
                    }
                
                memories_list.append(memory_dict)
            
            # Show memory previews in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE) and memories_list:
                log("Semantic memory results:", DebugLevel.VERBOSE)
                for i, memory in enumerate(memories_list[:3]):  # Show up to 3 memories
                    content_preview = debug_manager.truncate_content(memory.get("content", ""), 120)
                    importance = memory.get("importance", 5)
                    certainty = memory.get("certainty", 0.5)
                    log(f"  {i+1}. [semantic] {content_preview} (importance: {importance}, certainty: {certainty:.2f})", 
                       DebugLevel.VERBOSE)
                       
                if len(memories_list) > 3:
                    log(f"  ... and {len(memories_list) - 3} more", DebugLevel.VERBOSE)
            
            # Return the result
            response = {
                "memories": memories_list,
                "query": query_text,
                "total_found": len(memories_list)
            }
            
            if result.message:
                response["message"] = result.message
                
            return response
            
        except Exception as e:
            error_msg = f"Error retrieving semantic memories: {str(e)}"
            log_error(error_msg, "semantic_memory_retrieval")
            
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
                "error": str(e)
            }


class SemanticMemoryWriteTool(Tool):
    """Tool for creating semantic memories in Luna's memory store."""
    
    def __init__(self, memory_service: Optional[MemoryService] = None):
        """
        Initialize the semantic memory write tool with access to the memory service.
        
        Args:
            memory_service: Service for memory operations (can be set later via set_memory_service)
        """
        self.memory_service = memory_service
        super().__init__(
            name="write_semantic_memory",
            description="""Create a new semantic memory in Luna's memory store.

Semantic memories represent Luna's factual knowledge about the world, users, and learned information.
Use this tool to record important facts, knowledge, and information that Luna should remember.

This specialized tool provides additional parameters specific to semantic memories:
- Record the certainty level of the knowledge
- Specify the domain of knowledge
- Document the source of information
- Rate the reliability of the source

The memory will be stored in Luna's long-term memory for future recall and retrieval.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The semantic memory content to store"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance rating from 1 to 10",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "certainty": {
                        "type": "number",
                        "description": "Certainty level of this knowledge (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5
                    },
                    "verifiability": {
                        "type": "number",
                        "description": "How easily this knowledge can be verified (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5
                    },
                    "domain": {
                        "type": "string",
                        "description": "The domain or category of this knowledge",
                        "default": ""
                    },
                    "source": {
                        "type": "string",
                        "description": "The source of this information",
                        "default": ""
                    },
                    "source_reliability": {
                        "type": "number",
                        "description": "Reliability rating of the source (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.5
                    },
                    "emotion": {
                        "type": "object",
                        "description": "Emotional context associated with this memory (PAD model)",
                        "properties": {
                            "pleasure": {
                                "type": "number",
                                "description": "Pleasure dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0
                            },
                            "arousal": {
                                "type": "number",
                                "description": "Arousal dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0
                            },
                            "dominance": {
                                "type": "number",
                                "description": "Dominance dimension (-1.0 to 1.0)",
                                "minimum": -1.0,
                                "maximum": 1.0
                            }
                        }
                    },
                    "keywords": {
                        "type": "array",
                        "description": "Keywords to associate with this memory for better retrieval",
                        "items": {
                            "type": "string"
                        },
                        "default": []
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The user ID this memory is associated with"
                    }
                },
                "required": ["content"]
            },
            handler=self.handle,
            category=ToolCategory.MEMORY
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
        Process a semantic memory creation request.
        
        Args:
            tool_input: Dictionary containing memory data
            
        Returns:
            Dictionary containing operation result and metadata
        """
        try:
            content = tool_input.get("content", "")
            importance = tool_input.get("importance", 5)
            certainty = tool_input.get("certainty", 0.5)
            verifiability = tool_input.get("verifiability", 0.5)
            domain = tool_input.get("domain", "")
            source = tool_input.get("source", "")
            source_reliability = tool_input.get("source_reliability", 0.5)
            keywords = tool_input.get("keywords", [])
            user_id = tool_input.get("user_id")
            
            # Check if memory service is available
            if not self.memory_service:
                log_error("Memory service is not available", "semantic_memory_tool")
                return {
                    "success": False,
                    "error": "Memory service is not available. The memory system may not be initialized yet.",
                    "message": "Failed to store semantic memory: Memory service unavailable"
                }
            
            # Create emotional state if provided
            emotion = None
            if "emotion" in tool_input and tool_input["emotion"]:
                emotion_data = tool_input["emotion"]
                emotion = EmotionalState(
                    pleasure=emotion_data.get("pleasure"),
                    arousal=emotion_data.get("arousal"),
                    dominance=emotion_data.get("dominance")
                )
            
            # Create new semantic memory
            memory = SemanticMemory(
                content=content,
                importance=importance,
                certainty=certainty,
                verifiability=verifiability,
                domain=domain,
                source=source,
                source_reliability=source_reliability,
                keywords=keywords,
                user_id=user_id,
                emotion=emotion
            )
            
            # Store the memory
            memory_id = self.memory_service.store_memory(memory)
            
            if memory_id:
                log(f"Created semantic memory: '{content[:50]}...' | Importance: {importance}/10", 
                   DebugLevel.STANDARD, debug_manager.symbols.MEMORY)
                
                # Show more details in VERBOSE mode
                if debug_manager.should_debug(DebugLevel.VERBOSE):
                    details = []
                    if domain:
                        details.append(f"Domain: {domain}")
                    if source:
                        details.append(f"Source: {source}")
                    details.append(f"Certainty: {certainty:.2f}")
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
                    "memory_type": "semantic",
                    "importance": importance,
                    "message": f"Successfully stored semantic memory with ID {memory_id}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store memory",
                    "message": "Failed to store semantic memory"
                }
            
        except Exception as e:
            error_msg = f"Error writing semantic memory: {str(e)}"
            log_error(error_msg, "semantic_memory_storage")
            
            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)
                    
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create semantic memory: {str(e)}"
            }