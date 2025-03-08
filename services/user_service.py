"""
User service interface for Luna.

This module defines the interface for user management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from adapters.elasticsearch_adapter import ElasticsearchAdapter
from domain.models.memory import Memory, RelationshipMemory
from domain.models.user import (
    RelationshipStage,
    RelationshipUpdateRequest,
    StageHistory,
    TrustLevel,
    UserProfile,
    UserRelationship,
)


class UserService:
    """
    Interface for user management.

    This service manages user profiles, relationships, and user-related data.
    """

    def __init__(self, elasticsearch_adapter: ElasticsearchAdapter):
        """
        Initialize the UserService with the given elasticsearch adapter.

        Args:
            elasticsearch_adapter: Adapter for interacting with Elasticsearch
        """
        self.elasticsearch_adapter = elasticsearch_adapter

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by ID.

        Args:
            user_id: User identifier

        Returns:
            UserProfile: User profile or None if not found
        """
        return self.elasticsearch_adapter.get_user_profile(user_id)

    def create_or_get_user(
        self, user_id: str
    ) -> Tuple[bool, UserProfile, Optional[Dict[str, Any]]]:
        """
        Create a new user profile or get an existing one.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, UserProfile, Optional[Dict]]:
                is_new_user: Whether a new user was created
                user_profile: The user profile
                relationship_data: Any existing relationship data
        """
        # Check if user profile exists
        profile = self.get_user_profile(user_id)
        if profile is not None:
            # User exists, retrieve relationship
            relationship = self.elasticsearch_adapter.get_user_relationship(user_id)
            relationship = relationship if relationship else None
            return False, profile, relationship

        # Create new user profile
        profile = UserProfile(user_id=user_id)
        profile.interaction_meta.first_interaction = datetime.now()

        # Create new relationship
        relationship = UserRelationship(user_id=user_id)

        # Store both in Elasticsearch
        self.elasticsearch_adapter.store_user_profile(profile)
        self.elasticsearch_adapter.store_user_relationship(relationship)

        return True, profile, relationship.model_dump()

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Update a user profile.

        Args:
            user_id: User identifier
            updates: Dictionary of fields to update

        Returns:
            UserProfile: Updated user profile or None if update failed
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None

        # Apply updates to profile
        for key, value in updates.items():
            # Handle nested updates with dot notation
            if "." in key:
                parts = key.split(".")
                obj = profile
                for part in parts[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        break
                else:
                    # If we've navigated to the correct object, set the attribute
                    last_part = parts[-1]
                    if hasattr(obj, last_part):
                        setattr(obj, last_part, value)
            else:
                # Direct attribute update
                if hasattr(profile, key):
                    setattr(profile, key, value)

        # Store updated profile
        self.elasticsearch_adapter.store_user_profile(profile)
        return profile

    def update_user_relationship(
        self, request: RelationshipUpdateRequest
    ) -> Optional[UserRelationship]:
        """
        Update a user relationship with the data provided in the request.

        Args:
            request: Relationship update request containing fields to update

        Returns:
            UserRelationship: Updated relationship or None if update failed
        """
        user_id = request.user_id
        relationship = self.elasticsearch_adapter.get_user_relationship(user_id)

        if not relationship:
            # Create new relationship if one doesn't exist
            relationship = UserRelationship(user_id=user_id)

        # === Relationship Stage Updates ===
        if request.stage and request.stage != relationship.relationship_stage.current_stage:
            old_stage = relationship.relationship_stage.current_stage

            # Record stage history
            history_entry = StageHistory(
                stage=old_stage,
                started=relationship.relationship_stage.time_in_stage or "unknown",
                ended=datetime.now().isoformat(),
            )
            relationship.relationship_stage.stage_history.append(history_entry)

            # Update current stage
            relationship.relationship_stage.current_stage = request.stage
            relationship.relationship_stage.time_in_stage = datetime.now().isoformat()

            # Add progression notes if provided
            if request.relationship_update:
                relationship.relationship_stage.progression_notes = request.relationship_update

        # === Emotional Dynamics Updates ===

        # Update comfort level if provided
        if request.comfort_level is not None:
            relationship.emotional_dynamics.luna_comfort_level = request.comfort_level

        # Update trust level if provided
        if request.trust_level:
            relationship.emotional_dynamics.trust_level = request.trust_level

        # Emotional safety updates
        if request.sensitive_topics:
            for topic in request.sensitive_topics:
                if topic not in relationship.emotional_dynamics.emotional_safety.sensitive_topics:
                    relationship.emotional_dynamics.emotional_safety.sensitive_topics.append(topic)

        if request.approach_carefully:
            for topic in request.approach_carefully:
                if topic not in relationship.emotional_dynamics.emotional_safety.approach_carefully:
                    relationship.emotional_dynamics.emotional_safety.approach_carefully.append(
                        topic
                    )

        if request.avoid_topics:
            for topic in request.avoid_topics:
                if topic not in relationship.emotional_dynamics.emotional_safety.avoid:
                    relationship.emotional_dynamics.emotional_safety.avoid.append(topic)

        # Emotional resonance updates
        if request.positive_response_topics:
            for topic in request.positive_response_topics:
                if (
                    topic
                    not in relationship.emotional_dynamics.emotional_resonance.topics_with_positive_response
                ):
                    relationship.emotional_dynamics.emotional_resonance.topics_with_positive_response.append(
                        topic
                    )

        if request.deep_engagement_topics:
            for topic in request.deep_engagement_topics:
                if (
                    topic
                    not in relationship.emotional_dynamics.emotional_resonance.topics_with_deep_engagement
                ):
                    relationship.emotional_dynamics.emotional_resonance.topics_with_deep_engagement.append(
                        topic
                    )

        if request.tension_points:
            for topic in request.tension_points:
                if topic not in relationship.emotional_dynamics.emotional_resonance.tension_points:
                    relationship.emotional_dynamics.emotional_resonance.tension_points.append(topic)

        # Luna's emotional responses
        if request.joy_triggers:
            for trigger in request.joy_triggers:
                if (
                    trigger
                    not in relationship.emotional_dynamics.luna_emotional_responses.joy_triggers
                ):
                    relationship.emotional_dynamics.luna_emotional_responses.joy_triggers.append(
                        trigger
                    )

        if request.pride_moments:
            for moment in request.pride_moments:
                if (
                    moment
                    not in relationship.emotional_dynamics.luna_emotional_responses.pride_moments
                ):
                    relationship.emotional_dynamics.luna_emotional_responses.pride_moments.append(
                        moment
                    )

        if request.challenge_areas:
            for area in request.challenge_areas:
                if (
                    area
                    not in relationship.emotional_dynamics.luna_emotional_responses.challenge_areas
                ):
                    relationship.emotional_dynamics.luna_emotional_responses.challenge_areas.append(
                        area
                    )

        # === Conversation Patterns Updates ===

        # Add successful approach if provided
        if request.approach_category and request.approach_technique:
            if (
                request.approach_category
                not in relationship.conversation_patterns.successful_approaches
            ):
                relationship.conversation_patterns.successful_approaches[
                    request.approach_category
                ] = []

            if (
                request.approach_technique
                not in relationship.conversation_patterns.successful_approaches[
                    request.approach_category
                ]
            ):
                relationship.conversation_patterns.successful_approaches[
                    request.approach_category
                ].append(request.approach_technique)

        # Add communication adjustment if provided
        if (
            request.communication_area
            and request.communication_adjustment
            and request.communication_result
        ):
            from domain.models.user import CommunicationAdjustment

            adjustment = CommunicationAdjustment(
                area=request.communication_area,
                adjustment=request.communication_adjustment,
                result=request.communication_result,
            )
            relationship.conversation_patterns.communication_adjustments.append(adjustment)

        # Update conversation flow
        if request.typical_opening:
            if (
                request.typical_opening
                not in relationship.conversation_patterns.conversation_flow.typical_openings
            ):
                relationship.conversation_patterns.conversation_flow.typical_openings.append(
                    request.typical_opening
                )

        if request.conversation_depth:
            relationship.conversation_patterns.conversation_flow.depth_progression = (
                request.conversation_depth
            )

        if request.closing_pattern:
            relationship.conversation_patterns.conversation_flow.closing_patterns = (
                request.closing_pattern
            )

        if request.special_interaction_note:
            relationship.conversation_patterns.special_interaction_notes.append(
                request.special_interaction_note
            )

        # === Luna's Subjective Experience Updates ===

        # Update connection quality ratings
        if request.intellectual_connection is not None:
            relationship.luna_subjective_experience.connection_quality.intellectual = (
                request.intellectual_connection
            )

        if request.emotional_connection is not None:
            relationship.luna_subjective_experience.connection_quality.emotional = (
                request.emotional_connection
            )

        if request.creative_connection is not None:
            relationship.luna_subjective_experience.connection_quality.creative = (
                request.creative_connection
            )

        if request.overall_connection is not None:
            relationship.luna_subjective_experience.connection_quality.overall = (
                request.overall_connection
            )

        # Add growth through relationship if provided
        if request.growth_area and request.growth_insight and request.growth_impact:
            from domain.models.user import RelationshipGrowth

            growth = RelationshipGrowth(
                area=request.growth_area,
                insight=request.growth_insight,
                impact_on_luna=request.growth_impact,
            )
            relationship.luna_subjective_experience.growth_through_relationship.append(growth)

        # Update authenticity level
        if request.authenticity_level:
            relationship.luna_subjective_experience.authenticity_level.current_level = (
                request.authenticity_level
            )

        if request.authenticity_evolution:
            relationship.luna_subjective_experience.authenticity_level.evolution = (
                request.authenticity_evolution
            )

        if request.restricted_area:
            if (
                request.restricted_area
                not in relationship.luna_subjective_experience.authenticity_level.restricted_areas
            ):
                relationship.luna_subjective_experience.authenticity_level.restricted_areas.append(
                    request.restricted_area
                )

        # === Intervention Strategies Updates ===

        # Update anxiety response strategies
        if request.anxiety_recognition:
            relationship.intervention_strategies.anxiety_response.recognition_patterns.append(
                request.anxiety_recognition
            )

        if request.anxiety_approach:
            relationship.intervention_strategies.anxiety_response.effective_approaches.append(
                request.anxiety_approach
            )

        if request.anxiety_backfire_risk:
            relationship.intervention_strategies.anxiety_response.backfire_risks.append(
                request.anxiety_backfire_risk
            )

        # Update motivation support strategies
        if request.effective_encouragement:
            relationship.intervention_strategies.motivation_support.effective_encouragement.append(
                request.effective_encouragement
            )

        if request.accountability_preference:
            relationship.intervention_strategies.motivation_support.accountability_preferences = (
                request.accountability_preference
            )

        if request.celebration_style:
            relationship.intervention_strategies.motivation_support.celebration_style = (
                request.celebration_style
            )

        # Update conflict resolution strategies
        if request.misunderstanding_response:
            relationship.intervention_strategies.conflict_resolution.user_response_to_misunderstandings = (
                request.misunderstanding_response
            )

        if request.repair_approach:
            relationship.intervention_strategies.conflict_resolution.repair_approaches.append(
                request.repair_approach
            )

        if request.prevention_strategy:
            relationship.intervention_strategies.conflict_resolution.prevention_strategies = (
                request.prevention_strategy
            )

        # Save the updated relationship
        self.elasticsearch_adapter.store_user_relationship(relationship)

        return relationship

    def update_interaction_stats(self, user_id: str, increment: int = 1) -> bool:
        """
        Update interaction statistics for a user.

        Args:
            user_id: User identifier
            increment: Amount to increment interaction count

        Returns:
            bool: Whether the update was successful
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return False

        # Increment interaction count
        profile.interaction_meta.interaction_count += increment

        # Update profile
        result = self.elasticsearch_adapter.store_user_profile(profile)
        return result is not None

    def save_user_data(self, user_id: str) -> bool:
        """
        Save all user data to persistent storage.

        Args:
            user_id: User identifier

        Returns:
            bool: Whether the save was successful
        """
        # This is now a simple pass-through since Elasticsearch adapter
        # is already handling persistence for us
        profile = self.get_user_profile(user_id)
        relationship = self.elasticsearch_adapter.get_user_relationship(user_id)

        if not profile or not relationship:
            return False

        profile_result = self.elasticsearch_adapter.store_user_profile(profile)
        relationship_result = self.elasticsearch_adapter.store_user_relationship(relationship)

        return profile_result is not None and relationship_result is not None

    def _store_relationship_memory(
        self, user_id: str, content: str, memory_type: str, importance: int = 5
    ) -> str:
        """
        Helper method to store a relationship memory.

        Args:
            user_id: User identifier
            content: Memory content
            memory_type: Type of relationship memory
            importance: Importance level (1-10)

        Returns:
            str: Memory ID
        """
        memory = RelationshipMemory(
            content=content,
            memory_type="relationship",
            relationship_type=memory_type,
            importance=importance,
            user_id=user_id,
            closeness=0.7,
            trust=0.7,
            apprehension=0.3,
        )

        result = self.elasticsearch_adapter.store_memory(memory)
        return result.get("_id", "") if result else ""
