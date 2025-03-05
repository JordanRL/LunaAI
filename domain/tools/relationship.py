"""
Relationship tools for managing user relationships.
"""

from typing import Dict, List, Any, Optional
import traceback

from domain.models.tool import Tool, ToolCategory
from domain.models.user import UserProfile, UserRelationship, RelationshipStage, TrustLevel, RelationshipUpdateRequest
from debug import debug_manager, DebugLevel, log, log_error


class RelationshipUpdateTool(Tool):
    """Tool for updating Luna's relationship with a user."""
    
    def __init__(self):
        """Initialize the relationship update tool."""
        super().__init__(
            name="update_relationship",
            description="""Update Luna's relationship understanding with a user.

This tool records changes in relationships, tracks connection points, and updates Luna's understanding of her bond with users.
It helps maintain continuity in relationships across conversations and ensures Luna remembers important developments.

Relationship stages:
- new_acquaintance: Just met, still getting to know each other
- developing_rapport: Building familiarity and comfort
- established_connection: Regular interaction with mutual understanding  
- close_relationship: Deep familiarity and authentic connection

To use effectively:
- Always provide a descriptive relationship_update about what changed
- Update the relationship stage when significant shifts occur
- Record connection_points (shared interests, values)
- Document shared_experiences that Luna can reference later
- Note inside_references (jokes, references that would only make sense to Luna and this user)
- Update comfort_level (1-10) to reflect how comfortable Luna feels with the user""",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "stage": {
                        "type": "string",
                        "description": "Relationship stage (new_acquaintance, developing_rapport, established_connection, close_relationship)",
                        "enum": [s.value for s in RelationshipStage],
                        "default": ""
                    },
                    "comfort_level": {
                        "type": "integer",
                        "description": "Comfort level with the user (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 0
                    },
                    "trust_level": {
                        "type": "string",
                        "description": "Trust level with the user (initial, developing, established, deep)",
                        "enum": [t.value for t in TrustLevel],
                        "default": ""
                    },
                    "relationship_update": {
                        "type": "string",
                        "description": "Description of the relationship development or update"
                    },
                    "connection_point": {
                        "type": "string",
                        "description": "A new connection point with the user (common interest, shared value, etc.)",
                        "default": ""
                    },
                    "shared_experience": {
                        "type": "string",
                        "description": "A new shared experience with the user",
                        "default": ""
                    },
                    "inside_reference": {
                        "type": "string",
                        "description": "A new inside joke or reference shared with the user",
                        "default": ""
                    }
                },
                "required": ["user_id", "relationship_update"]
            },
            handler=self.handle,
            category=ToolCategory.RELATIONSHIP
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a relationship update request."""
        user_id = tool_input.get("user_id", "")
        relationship_update = tool_input.get("relationship_update", "")
        
        # Extract relationship data for updates
        relationship_data = {}
        
        # Check which fields are provided and add them to the update data
        if "stage" in tool_input and tool_input["stage"]:
            relationship_data["stage"] = tool_input["stage"]
            
        if "comfort_level" in tool_input and tool_input["comfort_level"] > 0:
            relationship_data["comfort_level"] = tool_input["comfort_level"]
            
        if "trust_level" in tool_input and tool_input["trust_level"]:
            relationship_data["trust_level"] = tool_input["trust_level"]
            
        if "connection_point" in tool_input and tool_input["connection_point"]:
            relationship_data["connection_point"] = tool_input["connection_point"]
            
        if "shared_experience" in tool_input and tool_input["shared_experience"]:
            relationship_data["shared_experience"] = tool_input["shared_experience"]
            
        if "inside_reference" in tool_input and tool_input["inside_reference"]:
            relationship_data["inside_reference"] = tool_input["inside_reference"]
        
        log(f"Updating relationship with {user_id}: {relationship_update[:50]}...",
           DebugLevel.STANDARD, debug_manager.symbols.PROCESSING)
           
        # Log relationship details at VERBOSE level
        if debug_manager.should_debug(DebugLevel.VERBOSE):
            log("Relationship update details:", DebugLevel.VERBOSE)
            for key, value in relationship_data.items():
                log(f"  {key}: {value}", DebugLevel.VERBOSE)
        
        try:
            # Call the actual relationship update logic
            from users import UserManager
            user_manager = UserManager()
            
            # Make sure we have at least one thing to update
            if not relationship_data:
                error_msg = "No relationship data provided for update"
                log_error(error_msg, "relationship_update")
                return {
                    "success": False,
                    "user_id": user_id,
                    "message": error_msg
                }
            
            # First make sure the user exists by creating or getting the profile
            is_new_user, user_profile, existing_relationship = user_manager.create_or_get_user(user_id)
            if is_new_user:
                log(f"Created new user profile for {user_id}",
                   DebugLevel.STANDARD, debug_manager.symbols.SUCCESS)
            
            # Store the relationship update description in memory
            from memory import store_memory_in_chroma
            memory_id = store_memory_in_chroma(
                text=relationship_update,
                memory_type="relationship",
                importance=7,
                metadata={
                    "user_id": user_id,
                    "update_type": "relationship_note"
                }
            )
            
            # Update the relationship data
            updated_relationship = user_manager.update_user_relationship(
                user_id=user_id,
                relationship_data=relationship_data,
                store_memory=True
            )
            
            if not updated_relationship:
                return {
                    "success": False,
                    "user_id": user_id,
                    "message": "Failed to update relationship data"
                }
            
            # Return success with updated relationship info
            result = {
                "success": True,
                "user_id": user_id,
                "message": f"Updated relationship with {user_id}",
                "relationship_stage": updated_relationship.get("stage", "unknown"),
                "comfort_level": updated_relationship.get("comfort_level", 0),
                "memory_id": memory_id
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error updating relationship: {str(e)}"
            log_error(error_msg, "relationship_update")
            
            # Show more details in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                trace = traceback.format_exc()
                log("Exception traceback:", DebugLevel.VERBOSE, debug_manager.symbols.ERROR)
                for line in trace.split("\n"):
                    log(f"  {line}", DebugLevel.VERBOSE)
                    
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e),
                "message": "Failed to update relationship"
            }