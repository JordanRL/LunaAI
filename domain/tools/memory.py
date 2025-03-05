"""
Memory-related tools for storing and retrieving memories.
"""

from typing import Dict, List, Any, Optional
import traceback

from domain.models.tool import Tool, ToolCategory
from domain.models.memory import Memory, MemoryQuery, MemoryResult
from debug import debug_manager, DebugLevel, log, log_error


class MemoryRetrieverTool(Tool):
    """Tool for retrieving memories from Luna's memory store."""
    
    def __init__(self):
        """Initialize the memory retriever tool."""
        super().__init__(
            name="retrieve_memory",
            description="""Retrieve memories from Luna's memory store based on a search query.

This tool searches Luna's memory for information about the user, past conversations, and learned facts.
It's useful when you need context about the user's preferences, history with Luna, or previously shared information.

Memory types available:
- episodic: Event-based memories (conversations, interactions)
- semantic: Factual knowledge about the user or world
- emotional: Luna's emotional responses and feelings
- relationship: Information about Luna's relationship with the user
- all: All memories, regardless of type

To use effectively:
- Provide specific search terms related to what you're looking for
- Specify memory_type if you only want certain types of memories
- Set an importance_threshold (1-10) to only get significant memories
- Set a reasonable limit (default is 5) to control how many results you get""",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to retrieve",
                        "default": 5
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory to retrieve",
                        "enum": ["episodic", "semantic", "emotional", "relationship", "all"],
                        "default": "all"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The user ID to retrieve memories for",
                        "default": ""
                    },
                    "importance_threshold": {
                        "type": "integer", 
                        "description": "Minimum importance level (1-10) of memories to retrieve",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 0
                    }
                },
                "required": ["query", "memory_type"]
            },
            handler=self.handle,
            category=ToolCategory.MEMORY
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a memory retrieval request."""
        query = tool_input.get("query", "")
        limit = tool_input.get("limit", 5)
        memory_type = tool_input.get("memory_type", "all")
        user_id = tool_input.get("user_id", "")
        importance_threshold = tool_input.get("importance_threshold", 0)
        
        log(f"Memory query: '{query}' | Type: {memory_type} | Limit: {limit}", 
           DebugLevel.STANDARD, debug_manager.symbols.MEMORY)
           
        # Log additional details in VERBOSE mode
        if debug_manager.should_debug(DebugLevel.VERBOSE):
            filter_details = []
            if user_id:
                filter_details.append(f"user_id: {user_id}")
            if importance_threshold > 0:
                filter_details.append(f"importance: ≥{importance_threshold}")
                
            if filter_details:
                log(f"  Filters: {', '.join(filter_details)}", DebugLevel.VERBOSE)
        
        # Call the actual memory retrieval logic
        try:
            log("Calling ChromaDB memory retrieval", DebugLevel.VERBOSE)
            from memory import get_memory_from_chroma
            
            # Build where clause for filtering
            where_clause = {}
            if user_id:
                where_clause["user_id"] = user_id
                
            if importance_threshold > 0:
                where_clause["importance"] = {"$gte": importance_threshold}
            
            # Only apply memory_type filter if not "all"
            mem_type_param = memory_type if memory_type != "all" else None
            
            # Retrieve memories from ChromaDB
            memory_results = get_memory_from_chroma(
                input_query=query,
                memory_type=mem_type_param,
                results=limit,
                importance_threshold=importance_threshold if importance_threshold > 0 else None,
                where=where_clause if where_clause else None
            )
            
            # Parse results into structured format
            memories = []
            if memory_results and "No relevant memories found" not in memory_results:
                memory_sections = memory_results.split("\n\n")
                
                for section in memory_sections:
                    if section.startswith("Memory"):
                        # Extract memory content and metadata
                        lines = section.split("\n")
                        content = "\n".join(lines[1:-1])  # Skip first and last lines
                        metadata_line = lines[-1] if len(lines) > 1 else ""
                        
                        # Parse metadata
                        metadata = {}
                        if metadata_line.startswith("[") and metadata_line.endswith("]"):
                            metadata_str = metadata_line[1:-1]  # Remove [ and ]
                            metadata_parts = metadata_str.split(", ")
                            
                            for part in metadata_parts:
                                if ": " in part:
                                    key, value = part.split(": ", 1)
                                    metadata[key] = value
                        
                        memory_type_value = metadata.get("memory_type", "unknown")
                        memories.append({
                            "content": content,
                            "type": memory_type_value,
                            "timestamp": metadata.get("timestamp", ""),
                            "importance": float(metadata.get("importance", "5")) / 10.0  # Convert from 1-10 to 0.0-1.0
                        })
            
            memory_count = len(memories)
            log(f"Found {memory_count} memories matching '{query}'", 
               DebugLevel.STANDARD, debug_manager.symbols.SUCCESS)
            
            # Show memory previews in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE) and memories:
                log("Memory results:", DebugLevel.VERBOSE)
                for i, memory in enumerate(memories[:3]):  # Show up to 3 memories
                    content_preview = debug_manager.truncate_content(memory.get("content", ""), 120)
                    memory_type = memory.get("type", "unknown")
                    importance = memory.get("importance", 0.5)
                    log(f"  {i+1}. [{memory_type}] {content_preview} (importance: {importance:.1f})", 
                       DebugLevel.VERBOSE)
                       
                if len(memories) > 3:
                    log(f"  ... and {len(memories) - 3} more", DebugLevel.VERBOSE)
            
            # If no memories found but query is substantive, return an empty result
            if not memories and len(query) > 3:
                log("No relevant memories found for substantive query", 
                   DebugLevel.STANDARD, debug_manager.symbols.INFO)
                return {
                    "memories": [],
                    "query": query,
                    "total_found": 0,
                    "message": "No relevant memories found"
                }
            
            # If no memories found with a very short query, return some fake starter memories
            # This is just to help bootstrap the system during initial testing
            if not memories and len(query) <= 3:
                log("Using fallback starter memories for bootstrapping", 
                   DebugLevel.STANDARD, debug_manager.symbols.INFO)
                memories = [
                    {"content": "User enjoys outdoor activities", "type": "semantic", "timestamp": "2024-01-01", "importance": 0.7},
                    {"content": "Luna introduced herself as a 22-year-old from Seattle", "type": "episodic", "timestamp": "2024-01-01", "importance": 0.8}
                ]
            
            return {
                "memories": memories[:limit],
                "query": query,
                "total_found": len(memories)
            }
            
        except Exception as e:
            error_msg = f"Error retrieving memories: {str(e)}"
            log_error(error_msg, "memory_retrieval")
            
            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)
            
            # Return empty result on error
            return {
                "memories": [],
                "query": query,
                "total_found": 0,
                "error": str(e)
            }


class MemoryWriterTool(Tool):
    """Tool for writing memories to Luna's memory store."""
    
    def __init__(self):
        """Initialize the memory writer tool."""
        super().__init__(
            name="write_memory",
            description="""Write a new memory to Luna's memory store.

This tool stores information in Luna's long-term memory for future recall.
It's useful for recording important facts, user preferences, emotional reactions, and relationship developments.

Memory types:
- episodic: Event-based memories (conversations, interactions)
- semantic: Factual knowledge
- emotional: Luna's emotional responses and feelings
- relationship: Information about relationships with users

Higher importance ratings (0-10) will make memories more likely to be retrieved in the future.
Adding keywords improves memory retrievability for specific topics.
Specifying an emotion helps organize memories by emotional context.""",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to store"
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory to store",
                        "enum": ["episodic", "semantic", "emotional", "relationship"]
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance rating from 0 to 10",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 5
                    },
                    "emotion": {
                        "type": "string",
                        "description": "Emotional context associated with this memory",
                        "default": ""
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
                        "description": "The user ID this memory is associated with",
                        "default": ""
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the memory",
                        "default": {}
                    }
                },
                "required": ["content", "memory_type"]
            },
            handler=self.handle,
            category=ToolCategory.MEMORY
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a memory writing request."""
        content = tool_input.get("content", "")
        memory_type = tool_input.get("memory_type", "episodic")
        importance = tool_input.get("importance", 5)
        emotion = tool_input.get("emotion", "")
        keywords = tool_input.get("keywords", [])
        user_id = tool_input.get("user_id", "")
        metadata = tool_input.get("metadata", {})
            
        log(f"Writing memory: '{content[:50]}...' | Type: {memory_type} | Importance: {importance}/10",
           DebugLevel.STANDARD, debug_manager.symbols.MEMORY)
           
        # Show more details in VERBOSE mode
        if debug_manager.should_debug(DebugLevel.VERBOSE):
            if emotion:
                log(f"  Emotion: {emotion}", DebugLevel.VERBOSE)
            if keywords:
                log(f"  Keywords: {', '.join(keywords)}", DebugLevel.VERBOSE)
            if user_id:
                log(f"  User ID: {user_id}", DebugLevel.VERBOSE)
        
        try:
            # Call the actual memory writing logic
            from memory import store_memory_in_chroma
            
            # Add user_id to metadata if provided
            if user_id:
                metadata["user_id"] = user_id
                
            # Call the real storage function
            memory_id = store_memory_in_chroma(
                text=content,
                memory_type=memory_type,
                emotion=emotion if emotion else None,
                importance=importance,
                keywords=keywords if keywords else None,
                metadata=metadata if metadata else None
            )
            
            return {
                "success": True,
                "memory_id": memory_id,
                "memory_type": memory_type,
                "importance": importance,
                "message": f"Successfully stored {memory_type} memory with ID {memory_id}"
            }
            
        except Exception as e:
            error_msg = f"Error writing memory: {str(e)}"
            log_error(error_msg, "memory_storage")
            
            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)
                    
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to store memory: {str(e)}"
            }