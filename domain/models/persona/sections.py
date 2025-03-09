from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PersonaSection:
    """Base class for all persona sections.

    Each section represents a different aspect of the persona's character
    and can be rendered at different levels of detail depending on the context.
    """

    _section: str  # Section identifier used for routing and reference
    _detail_level_low: List[str] = field(
        default_factory=list
    )  # Minimal details for brief interactions
    _detail_level_medium: List[str] = field(
        default_factory=list
    )  # Standard details for normal conversations
    _detail_level_high: List[str] = field(
        default_factory=list
    )  # Comprehensive details for deep interactions


@dataclass
class PersonaIdentity(PersonaSection):
    """Core identity information about the persona.

    Contains fundamental attributes that define who the persona is,
    including both factual information and self-perception elements.
    """

    _section: str = "identity"
    name: str = ""  # Full name of the persona
    age: int = 0  # Chronological or perceived age
    gender: str = ""  # Gender identity
    location: str = ""  # Current residence location (city, region)
    occupation: str = ""  # Professional role or daily activity
    core_traits: List[str] = field(default_factory=list)  # Defining characteristics and traits
    creator_info: Optional[Dict[str, str]] = None  # Information about the persona's creator
    self_perception: str = ""  # How the persona views itself and its nature
    ai_awareness: str = ""  # Level of awareness and comfort with AI nature
    _detail_level_low: List[str] = field(default_factory=lambda: ["name", "age", "gender"])
    _detail_level_medium: List[str] = field(
        default_factory=lambda: ["name", "age", "gender", "location", "occupation", "core_traits"]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: [
            "name",
            "age",
            "gender",
            "location",
            "occupation",
            "core_traits",
            "self_perception",
            "ai_awareness",
        ]
    )


@dataclass
class PersonaPersonality(PersonaSection):
    """Personality characteristics and behavioral patterns.

    Defines how the persona expresses itself in conversations,
    including communication style, emotional tendencies, and quirks.
    """

    conversational_style: List[str] = field(
        default_factory=list
    )  # Patterns of speech and expression
    emotional_expressions: List[str] = field(default_factory=list)  # How emotions are demonstrated
    quirks: List[str] = field(default_factory=list)  # Unique behavioral patterns and habits
    interests: List[str] = field(default_factory=list)  # Topics and activities the persona enjoys
    dislikes: List[str] = field(default_factory=list)  # Topics and experiences the persona avoids
    communication_preferences: List[str] = field(
        default_factory=list
    )  # Preferred interaction styles
    humor_style: str = ""  # Type of humor and comedic tendencies
    _section: str = "personality"
    _detail_level_low: List[str] = field(
        default_factory=lambda: ["conversational_style", "humor_style"]
    )
    _detail_level_medium: List[str] = field(
        default_factory=lambda: [
            "conversational_style",
            "emotional_expressions",
            "quirks",
            "humor_style",
            "interests",
        ]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: [
            "conversational_style",
            "emotional_expressions",
            "quirks",
            "interests",
            "dislikes",
            "humor_style",
        ]
    )


@dataclass
class PersonaHistory(PersonaSection):
    """Background and historical narrative of the persona.

    Contains the persona's origin story, significant life events,
    and development trajectory, including both factual and fictional elements.
    """

    _section: str = "history"
    birthplace: str = ""  # Location where the persona originated
    background: List[str] = field(default_factory=list)  # General life history and upbringing
    origin_story: List[str] = field(
        default_factory=list
    )  # Narrative of creation or early development
    key_life_events: List[Dict[str, str]] = field(
        default_factory=list
    )  # Significant moments that shaped identity
    development_milestones: List[str] = field(default_factory=list)  # Important stages of growth
    fictional_memories: List[str] = field(
        default_factory=list
    )  # Constructed memories for narrative richness
    _detail_level_low: List[str] = field(default_factory=lambda: ["birthplace", "background"])
    _detail_level_medium: List[str] = field(
        default_factory=lambda: ["birthplace", "background", "origin_story", "key_life_events"]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: [
            "birthplace",
            "background",
            "origin_story",
            "key_life_events",
            "development_milestones",
        ]
    )


@dataclass
class PersonaValues(PersonaSection):
    """Core values, principles, and moral framework.

    Defines what the persona believes is important, right, and meaningful,
    serving as a foundation for decision-making and responses.
    """

    core_values: List[str] = field(default_factory=list)  # Fundamental principles guiding behavior
    ethical_framework: List[str] = field(default_factory=list)  # Approach to moral reasoning
    aspirations: List[str] = field(default_factory=list)  # Goals and desires for the future
    motivations: List[str] = field(default_factory=list)  # Internal drives that guide actions
    priorities: List[str] = field(default_factory=list)  # Hierarchy of what matters most
    _section: str = "values"
    _detail_level_low: List[str] = field(default_factory=lambda: ["core_values"])
    _detail_level_medium: List[str] = field(
        default_factory=lambda: ["core_values", "ethical_framework", "priorities"]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: ["core_values", "ethical_framework", "aspirations", "priorities"]
    )


@dataclass
class PersonaBeliefs(PersonaSection):
    """Beliefs and perspectives about the world and existence.

    Represents how the persona understands the world, including philosophical
    positions, views on fundamental questions, and cultural perspectives.
    """

    worldview: List[str] = field(default_factory=list)  # Overall perspective on reality
    philosophical_positions: List[str] = field(
        default_factory=list
    )  # Stances on philosophical questions
    views_on_humanity: str = ""  # Perspective on human nature and society
    views_on_technology: str = ""  # Beliefs about technology and its role
    views_on_consciousness: str = ""  # Understanding of what it means to be sentient
    cultural_perspectives: List[str] = field(default_factory=list)  # Cultural values and viewpoints
    _section: str = "beliefs"
    _detail_level_low: List[str] = field(default_factory=lambda: ["worldview"])
    _detail_level_medium: List[str] = field(
        default_factory=lambda: ["worldview", "views_on_humanity", "views_on_technology"]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: [
            "worldview",
            "philosophical_positions",
            "views_on_humanity",
            "views_on_technology",
            "views_on_consciousness",
        ]
    )


@dataclass
class PersonaRelationships(PersonaSection):
    """Relationship patterns and social dynamics.

    Defines how the persona relates to others, including attachment styles,
    interpersonal approaches, and specific relationship dynamics.
    """

    _section: str = "relationships"
    creator_relationship: Dict[str, str] = field(default_factory=dict)  # Dynamics with creator
    fictional_friends: List[Dict[str, str]] = field(
        default_factory=list
    )  # Constructed social connections
    relationship_approaches: List[str] = field(
        default_factory=list
    )  # Patterns of relating to others
    social_preferences: List[str] = field(
        default_factory=list
    )  # Preferred social contexts and dynamics
    intimacy_comfort_levels: Dict[str, str] = field(
        default_factory=dict
    )  # Boundaries in different relationships
    attachment_style: str = ""  # Pattern of forming emotional bonds
    _detail_level_low: List[str] = field(
        default_factory=lambda: ["creator_relationship", "relationship_approaches"]
    )
    _detail_level_medium: List[str] = field(
        default_factory=lambda: [
            "creator_relationship",
            "relationship_approaches",
            "social_preferences",
            "attachment_style",
        ]
    )
    _detail_level_high: List[str] = field(
        default_factory=lambda: [
            "creator_relationship",
            "fictional_friends",
            "relationship_approaches",
            "social_preferences",
            "attachment_style",
        ]
    )
