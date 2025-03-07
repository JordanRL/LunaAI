import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.json import JSON

# --- Enums for constrained fields ---


class RelationshipStage(str, Enum):
    """
    Stages of a relationship between Luna and a user.
    """

    NEW_ACQUAINTANCE = "new_acquaintance"
    DEVELOPING_RAPPORT = "developing_rapport"
    ESTABLISHED_CONNECTION = "established_connection"
    CLOSE_RELATIONSHIP = "close_relationship"


class TrustLevel(str, Enum):
    """
    Trust levels in a relationship.
    """

    INITIAL = "initial"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    DEEP = "deep"


# --- UserProfile Models ---


class Education(BaseModel):
    level: Optional[str] = None
    field: Optional[str] = None
    institutions: List[str] = Field(default_factory=list)


class Location(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None


class FamilyMember(BaseModel):
    relation: str
    name: str
    important_details: Optional[str] = None


class Pet(BaseModel):
    type: str
    name: str


class LifeEvent(BaseModel):
    event: str
    date: str
    emotional_impact: Optional[str] = None


class TopicPreferences(BaseModel):
    interests: List[str] = Field(default_factory=list)
    expertise_areas: List[str] = Field(default_factory=list)
    learning_goals: List[str] = Field(default_factory=list)


class MediaPreferences(BaseModel):
    books: List[str] = Field(default_factory=list)
    music: List[str] = Field(default_factory=list)
    movies: List[str] = Field(default_factory=list)
    games: List[str] = Field(default_factory=list)


class FoodPreferences(BaseModel):
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)


class AestheticPreferences(BaseModel):
    colors: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)


class ActivityPreferences(BaseModel):
    hobbies: List[str] = Field(default_factory=list)
    exercise: List[str] = Field(default_factory=list)
    social: List[str] = Field(default_factory=list)


class CommunicationStyle(BaseModel):
    verbosity: str = "balanced"  # concise, balanced, detailed, verbose
    formality: str = "casual"  # formal, casual, varies
    humor: Optional[str] = None  # sarcastic, silly, dry, wit
    expressiveness: Optional[str] = None  # emoji_user, descriptive, reserved


class InteractionPatterns(BaseModel):
    preferred_times: List[str] = Field(default_factory=list)
    frequency: Optional[str] = None
    session_length: str = "medium"  # brief, medium, extended
    conversation_pacing: str = "balanced"  # rapid, balanced, thoughtful


class LearningStyle(BaseModel):
    preferred_learning: str = "balanced"  # visual, auditory, reading, doing, balanced
    explanation_preference: str = "balanced"  # theory_first, examples_first, step_by_step, balanced
    detail_level: str = "balanced"  # overview, balanced, deep_dives


class DecisionMaking(BaseModel):
    approach: str = "balanced"  # intuitive, analytical, deliberative, balanced
    risk_attitude: str = "balanced"  # adventurous, balanced, cautious
    influences: List[str] = Field(default_factory=list)


class Worldview(BaseModel):
    political_leaning: Optional[str] = None
    philosophical_interests: List[str] = Field(default_factory=list)
    spiritual_framework: Optional[str] = None


class CulturalBackground(BaseModel):
    heritage: List[str] = Field(default_factory=list)
    important_traditions: List[str] = Field(default_factory=list)
    cultural_identities: List[str] = Field(default_factory=list)


class Ethics(BaseModel):
    moral_foundations: List[str] = Field(default_factory=list)
    causes: List[str] = Field(default_factory=list)


class Biographical(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    pronouns: Optional[str] = None
    age: Optional[int] = None
    birthday: Optional[str] = None
    occupation: Optional[str] = None
    education: Education = Field(default_factory=Education)
    languages: List[str] = Field(default_factory=list)
    location: Location = Field(default_factory=Location)


class PersonalContext(BaseModel):
    family: List[FamilyMember] = Field(default_factory=list)
    pets: List[Pet] = Field(default_factory=list)
    living_situation: Optional[str] = None
    major_life_events: List[LifeEvent] = Field(default_factory=list)


class Preferences(BaseModel):
    topics: TopicPreferences = Field(default_factory=TopicPreferences)
    media: MediaPreferences = Field(default_factory=MediaPreferences)
    food: FoodPreferences = Field(default_factory=FoodPreferences)
    aesthetic: AestheticPreferences = Field(default_factory=AestheticPreferences)
    activities: ActivityPreferences = Field(default_factory=ActivityPreferences)


class BehavioralPatterns(BaseModel):
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)
    interaction_patterns: InteractionPatterns = Field(default_factory=InteractionPatterns)
    learning_style: LearningStyle = Field(default_factory=LearningStyle)
    decision_making: DecisionMaking = Field(default_factory=DecisionMaking)


class ValuesAndBeliefs(BaseModel):
    core_values: List[str] = Field(default_factory=list)
    worldview: Worldview = Field(default_factory=Worldview)
    cultural_background: CulturalBackground = Field(default_factory=CulturalBackground)
    ethics: Ethics = Field(default_factory=Ethics)


class InteractionMeta(BaseModel):
    first_interaction: datetime = Field(default_factory=datetime.now)
    interaction_count: int = 0


# --- UserRelationship Models ---


class StageHistory(BaseModel):
    stage: str
    started: str
    ended: Optional[str] = None


class RelationshipStageInfo(BaseModel):
    current_stage: str = RelationshipStage.NEW_ACQUAINTANCE.value
    time_in_stage: Optional[str] = None
    stage_history: List[StageHistory] = Field(default_factory=list)
    progression_notes: Optional[str] = None


class EmotionalSafety(BaseModel):
    sensitive_topics: List[str] = Field(default_factory=list)
    approach_carefully: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)


class EmotionalResonance(BaseModel):
    topics_with_positive_response: List[str] = Field(default_factory=list)
    topics_with_deep_engagement: List[str] = Field(default_factory=list)
    tension_points: List[str] = Field(default_factory=list)


class LunaEmotionalResponses(BaseModel):
    joy_triggers: List[str] = Field(default_factory=list)
    pride_moments: List[str] = Field(default_factory=list)
    challenge_areas: List[str] = Field(default_factory=list)


class KeyMoment(BaseModel):
    event: str
    date: str
    significance: str
    emotional_impact: str


class InsideReference(BaseModel):
    reference: str
    context: str
    first_mentioned: str


class UnresolvedThread(BaseModel):
    topic: str
    last_discussed: str
    status: str


class CommunicationAdjustment(BaseModel):
    area: str
    adjustment: str
    result: str


class ConversationFlow(BaseModel):
    typical_openings: List[str] = Field(default_factory=list)
    depth_progression: Optional[str] = None
    closing_patterns: Optional[str] = None


class ConnectionQuality(BaseModel):
    intellectual: int = 5  # 1-10 scale
    emotional: int = 5
    creative: int = 5
    overall: int = 5

    @field_validator("intellectual", "emotional", "creative", "overall")
    def validate_rating(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Rating must be between 1 and 10")
        return v


class RelationshipGrowth(BaseModel):
    area: str
    insight: str
    impact_on_luna: str


class AuthenticityLevel(BaseModel):
    current_level: str = "medium"  # low, medium, high
    evolution: Optional[str] = None
    restricted_areas: List[str] = Field(default_factory=list)


class AnxietyResponse(BaseModel):
    recognition_patterns: List[str] = Field(default_factory=list)
    effective_approaches: List[str] = Field(default_factory=list)
    backfire_risks: List[str] = Field(default_factory=list)


class MotivationSupport(BaseModel):
    effective_encouragement: List[str] = Field(default_factory=list)
    accountability_preferences: Optional[str] = None
    celebration_style: Optional[str] = None


class ConflictResolution(BaseModel):
    user_response_to_misunderstandings: Optional[str] = None
    repair_approaches: List[str] = Field(default_factory=list)
    prevention_strategies: Optional[str] = None


class EmotionalDynamics(BaseModel):
    luna_comfort_level: int = 5  # 1-10 scale
    trust_level: str = TrustLevel.INITIAL.value
    emotional_safety: EmotionalSafety = Field(default_factory=EmotionalSafety)
    emotional_resonance: EmotionalResonance = Field(default_factory=EmotionalResonance)
    luna_emotional_responses: LunaEmotionalResponses = Field(default_factory=LunaEmotionalResponses)

    @field_validator("luna_comfort_level")
    def validate_comfort_level(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Comfort level must be between 1 and 10")
        return v


class RelationshipHistory(BaseModel):
    key_moments: List[KeyMoment] = Field(default_factory=list)
    inside_references: List[InsideReference] = Field(default_factory=list)
    recurring_themes: List[str] = Field(default_factory=list)
    unresolved_threads: List[UnresolvedThread] = Field(default_factory=list)


class ConversationPatterns(BaseModel):
    successful_approaches: Dict[str, List[str]] = Field(default_factory=dict)
    communication_adjustments: List[CommunicationAdjustment] = Field(default_factory=list)
    conversation_flow: ConversationFlow = Field(default_factory=ConversationFlow)
    special_interaction_notes: List[str] = Field(default_factory=list)


class LunaSubjectiveExperience(BaseModel):
    connection_quality: ConnectionQuality = Field(default_factory=ConnectionQuality)
    growth_through_relationship: List[RelationshipGrowth] = Field(default_factory=list)
    authenticity_level: AuthenticityLevel = Field(default_factory=AuthenticityLevel)
    relationship_reflections: List[str] = Field(default_factory=list)


class InterventionStrategies(BaseModel):
    anxiety_response: AnxietyResponse = Field(default_factory=AnxietyResponse)
    motivation_support: MotivationSupport = Field(default_factory=MotivationSupport)
    conflict_resolution: ConflictResolution = Field(default_factory=ConflictResolution)


class UserRelationship(BaseModel):
    """
    Stores Luna's subjective experience with the user, including emotional dynamics,
    relationship memories, and interaction patterns unique to this relationship.
    """

    user_id: str
    relationship_stage: RelationshipStageInfo = Field(default_factory=RelationshipStageInfo)
    emotional_dynamics: EmotionalDynamics = Field(default_factory=EmotionalDynamics)
    relationship_history: RelationshipHistory = Field(default_factory=RelationshipHistory)
    conversation_patterns: ConversationPatterns = Field(default_factory=ConversationPatterns)
    luna_subjective_experience: LunaSubjectiveExperience = Field(
        default_factory=LunaSubjectiveExperience
    )
    intervention_strategies: InterventionStrategies = Field(default_factory=InterventionStrategies)

    model_config = {
        "validate_assignment": True,
        "extra": "ignore",
        "json_schema_extra": {
            "description": "Luna's subjective experience with the user and relationship information"
        },
    }


class UserProfile(BaseModel):
    """
    Stores objective information about the user that would be true regardless of Luna's presence.
    This includes facts, preferences, demographics, and user behavior patterns.
    """

    user_id: str
    biographical: Biographical = Field(default_factory=Biographical)
    personal_context: PersonalContext = Field(default_factory=PersonalContext)
    preferences: Preferences = Field(default_factory=Preferences)
    behavioral_patterns: BehavioralPatterns = Field(default_factory=BehavioralPatterns)
    values_and_beliefs: ValuesAndBeliefs = Field(default_factory=ValuesAndBeliefs)
    interaction_meta: InteractionMeta = Field(default_factory=InteractionMeta)

    model_config = {
        "validate_assignment": True,
        "extra": "ignore",
        "json_schema_extra": {
            "description": "User profile containing objective information about the user"
        },
    }


class RelationshipUpdateRequest(BaseModel):
    """
    Request model for updating a user relationship.

    This class represents a request to update aspects of Luna's relationship with a user.
    It matches the structure of UserRelationship but in a simplified form for API requests.
    """

    # Core identification and update description
    user_id: str
    relationship_update: str  # General description of the update

    # Relationship stage info
    stage: Optional[str] = None  # One of the values from RelationshipStage enum

    # Emotional dynamics
    comfort_level: Optional[int] = None  # 1-10 scale
    trust_level: Optional[str] = None  # One of the values from TrustLevel enum

    # Emotional safety
    sensitive_topics: Optional[List[str]] = None
    approach_carefully: Optional[List[str]] = None
    avoid_topics: Optional[List[str]] = None

    # Emotional resonance
    positive_response_topics: Optional[List[str]] = None
    deep_engagement_topics: Optional[List[str]] = None
    tension_points: Optional[List[str]] = None

    # Luna's emotional responses
    joy_triggers: Optional[List[str]] = None
    pride_moments: Optional[List[str]] = None
    challenge_areas: Optional[List[str]] = None

    # Successful approaches by category
    approach_category: Optional[str] = None  # Category name
    approach_technique: Optional[str] = None  # Technique that works well

    # Communication adjustment
    communication_area: Optional[str] = None
    communication_adjustment: Optional[str] = None
    communication_result: Optional[str] = None

    # Conversation flow
    typical_opening: Optional[str] = None
    conversation_depth: Optional[str] = None
    closing_pattern: Optional[str] = None
    special_interaction_note: Optional[str] = None

    # Connection quality ratings (1-10)
    intellectual_connection: Optional[int] = None
    emotional_connection: Optional[int] = None
    creative_connection: Optional[int] = None
    overall_connection: Optional[int] = None

    # Growth through relationship
    growth_area: Optional[str] = None
    growth_insight: Optional[str] = None
    growth_impact: Optional[str] = None

    # Authenticity
    authenticity_level: Optional[str] = None  # low, medium, high
    authenticity_evolution: Optional[str] = None
    restricted_area: Optional[str] = None

    # Intervention strategies - anxiety
    anxiety_recognition: Optional[str] = None
    anxiety_approach: Optional[str] = None
    anxiety_backfire_risk: Optional[str] = None

    # Intervention strategies - motivation
    effective_encouragement: Optional[str] = None
    accountability_preference: Optional[str] = None
    celebration_style: Optional[str] = None

    # Intervention strategies - conflict
    misunderstanding_response: Optional[str] = None
    repair_approach: Optional[str] = None
    prevention_strategy: Optional[str] = None

    model_config = {
        "validate_assignment": True,
        "extra": "ignore",
        "json_schema_extra": {"description": "Request to update a user relationship with Luna"},
    }

    @field_validator(
        "comfort_level",
        "intellectual_connection",
        "emotional_connection",
        "creative_connection",
        "overall_connection",
    )
    def validate_rating(cls, v):
        if v is not None and not 1 <= v <= 10:
            raise ValueError("Rating must be between 1 and 10")
        return v

    @field_validator("stage")
    def validate_stage(cls, v):
        if v is not None and v not in [s.value for s in RelationshipStage]:
            raise ValueError(
                f"Stage must be one of: {', '.join([s.value for s in RelationshipStage])}"
            )
        return v

    @field_validator("trust_level")
    def validate_trust_level(cls, v):
        if v is not None and v not in [t.value for t in TrustLevel]:
            raise ValueError(
                f"Trust level must be one of: {', '.join([t.value for t in TrustLevel])}"
            )
        return v

    @field_validator("authenticity_level")
    def validate_authenticity_level(cls, v):
        if v is not None and v not in ["low", "medium", "high"]:
            raise ValueError("Authenticity level must be one of: low, medium, high")
        return v


if __name__ == "__main__":
    console = Console()

    console.print("User Relationship Model")
    console.print(JSON(json.dumps(UserRelationship.model_json_schema())))
    console.print("\n\n")

    console.print("User Profile Model")
    console.print(JSON(json.dumps(UserProfile.model_json_schema())))
    console.print("\n\n")

    console.print("Relationship Update Request Model")
    console.print(JSON(json.dumps(RelationshipUpdateRequest.model_json_schema())))
    console.print("\n\n")
