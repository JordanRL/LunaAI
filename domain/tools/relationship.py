"""
Relationship tools for managing user relationships.
"""

from typing import Any, Dict, List, Optional

from domain.models.tool import Tool, ToolCategory
from domain.models.user import (
    RelationshipStage,
    RelationshipUpdateRequest,
    TrustLevel,
    UserProfile,
    UserRelationship,
)
from services.user_service import UserService


class RelationshipUpdateTool(Tool):
    """Tool for updating Luna's relationship with a user."""

    def __init__(self, user_service: UserService):
        """Initialize the relationship update tool."""
        self.user_service = user_service
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

This tool supports a rich relationship model with the following categories of data:
- Relationship stage and comfort level: How the relationship is developing
- Emotional dynamics: How Luna feels with this user
- Relationship history: Key moments and shared context
- Conversation patterns: What communication approaches work best
- Luna's subjective experience: How Luna perceives the relationship
- Intervention strategies: How to handle various user emotional states

Core fields:
- user_id: The user identifier
- stage: Relationship stage (new_acquaintance, developing_rapport, established_connection, close_relationship)
- comfort_level: Comfort level with the user (1-10)
- trust_level: Trust level with the user (initial, developing, established, deep)

See the full schema for additional fields that can be used to provide detailed relationship data.""",
            input_schema={
                "type": "object",
                "properties": {
                    # Core identification
                    "user_id": {"type": "string", "description": "User identifier"},
                    # Relationship stage
                    "stage": {
                        "type": "string",
                        "description": "Relationship stage (new_acquaintance, developing_rapport, established_connection, close_relationship)",
                        "enum": [s.value for s in RelationshipStage],
                    },
                    # Emotional dynamics
                    "comfort_level": {
                        "type": "integer",
                        "description": "Comfort level with the user (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "trust_level": {
                        "type": "string",
                        "description": "Trust level with the user (initial, developing, established, deep)",
                        "enum": [t.value for t in TrustLevel],
                    },
                    # Emotional safety topics
                    "sensitive_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics that are sensitive for this user",
                    },
                    "approach_carefully": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics to approach with care for this user",
                    },
                    "avoid_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics to avoid with this user",
                    },
                    # Emotional resonance
                    "positive_response_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics that trigger positive responses",
                    },
                    "deep_engagement_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics that lead to deep engagement",
                    },
                    "tension_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics that create tension",
                    },
                    # Luna's emotional responses
                    "joy_triggers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "What brings Luna joy with this user",
                    },
                    "pride_moments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Moments that make Luna feel proud",
                    },
                    "challenge_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Areas that challenge Luna with this user",
                    },
                    # Successful approaches
                    "approach_category": {
                        "type": "string",
                        "description": "Category of successful approach (e.g., 'explanation', 'emotional_support')",
                    },
                    "approach_technique": {
                        "type": "string",
                        "description": "Specific technique that works well in that category",
                    },
                    # Communication adjustment
                    "communication_area": {
                        "type": "string",
                        "description": "Area of communication that needed adjustment",
                    },
                    "communication_adjustment": {
                        "type": "string",
                        "description": "How Luna adjusted communication",
                    },
                    "communication_result": {
                        "type": "string",
                        "description": "Result of the communication adjustment",
                    },
                    # Conversation flow
                    "typical_opening": {
                        "type": "string",
                        "description": "Typical conversation opening with this user",
                    },
                    "conversation_depth": {
                        "type": "string",
                        "description": "How conversations typically progress in depth",
                    },
                    "closing_pattern": {
                        "type": "string",
                        "description": "How conversations typically conclude",
                    },
                    "special_interaction_note": {
                        "type": "string",
                        "description": "Special note about interactions with this user",
                    },
                    # Connection quality
                    "intellectual_connection": {
                        "type": "integer",
                        "description": "Intellectual connection quality (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "emotional_connection": {
                        "type": "integer",
                        "description": "Emotional connection quality (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "creative_connection": {
                        "type": "integer",
                        "description": "Creative connection quality (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "overall_connection": {
                        "type": "integer",
                        "description": "Overall connection quality (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                    # Growth through relationship
                    "growth_area": {
                        "type": "string",
                        "description": "Area of Luna's growth through this relationship",
                    },
                    "growth_insight": {
                        "type": "string",
                        "description": "Insight Luna gained in this area",
                    },
                    "growth_impact": {
                        "type": "string",
                        "description": "How this growth impacted Luna",
                    },
                    # Authenticity
                    "authenticity_level": {
                        "type": "string",
                        "description": "Current authenticity level (low, medium, high)",
                        "enum": ["low", "medium", "high"],
                    },
                    "authenticity_evolution": {
                        "type": "string",
                        "description": "How authenticity has evolved in this relationship",
                    },
                    "restricted_area": {
                        "type": "string",
                        "description": "Area where Luna restricts authenticity",
                    },
                    # Intervention strategies - anxiety
                    "anxiety_recognition": {
                        "type": "string",
                        "description": "Pattern for recognizing user anxiety",
                    },
                    "anxiety_approach": {
                        "type": "string",
                        "description": "Effective approach for user anxiety",
                    },
                    "anxiety_backfire_risk": {
                        "type": "string",
                        "description": "Risk of intervention backfiring",
                    },
                    # Intervention strategies - motivation
                    "effective_encouragement": {
                        "type": "string",
                        "description": "Effective encouragement approach",
                    },
                    "accountability_preference": {
                        "type": "string",
                        "description": "User's accountability preference",
                    },
                    "celebration_style": {
                        "type": "string",
                        "description": "User's preferred celebration style",
                    },
                    # Intervention strategies - conflict
                    "misunderstanding_response": {
                        "type": "string",
                        "description": "How user responds to misunderstandings",
                    },
                    "repair_approach": {
                        "type": "string",
                        "description": "Effective approach for repairing misunderstandings",
                    },
                    "prevention_strategy": {
                        "type": "string",
                        "description": "Strategy for preventing misunderstandings",
                    },
                },
                "required": ["user_id"],
            },
            handler=self.handle,
            category=ToolCategory.RELATIONSHIP,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a relationship update request."""
        user_id = tool_input.get("user_id", "")
        relationship_update = tool_input.get("relationship_update", "")

        try:
            # Create relationship update request directly from tool_input
            # This will pass all provided fields to the request object
            update_request = RelationshipUpdateRequest(
                user_id=user_id, relationship_update=relationship_update
            )

            # Copy any additional fields from tool_input to update_request
            for key, value in tool_input.items():
                if key not in ["user_id", "relationship_update"] and value:
                    if hasattr(update_request, key):
                        setattr(update_request, key, value)

            # Update the relationship data - this will also store the memory
            updated_relationship = self.user_service.update_user_relationship(update_request)
            memory_id = "stored_with_relationship"  # The memory is now stored by the UserService

            if not updated_relationship:
                return {
                    "success": False,
                    "user_id": user_id,
                    "message": "Failed to update relationship data",
                }

            # Return success with updated relationship info
            result = {
                "success": True,
                "user_id": user_id,
                "message": f"Updated relationship with {user_id}",
                "relationship_stage": updated_relationship.relationship_stage.current_stage,
                "comfort_level": updated_relationship.emotional_dynamics.luna_comfort_level,
                "trust_level": updated_relationship.emotional_dynamics.trust_level,
                "memory_id": memory_id,
            }

            return result
        except Exception:
            return {
                "success": False,
                "user_id": user_id,
                "message": "Failed to update relationship",
            }
