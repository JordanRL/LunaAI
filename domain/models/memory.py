import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from domain.models.emotion import EmotionalState


@dataclass
class Memory:
    """
    Represents a memory in Luna's memory system.

    Attributes:
        content: The actual memory content (text)
        memory_type: Type of memory (episodic, semantic, emotional, relationship)
        importance: Importance rating from 1-10
        timestamp: When the memory was created
        emotion: Emotional context associated with this memory
        keywords: Keywords for better retrieval
        user_id: The user this memory is associated with
        id: Unique identifier (assigned by storage service)
    """

    content: str
    memory_type: str  # episodic, semantic, emotional, relationship
    importance: int = 5
    timestamp: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    user_id: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    emotion: Optional[EmotionalState] = None

    def to_document(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            "last_accessed": (
                self.last_accessed.isoformat()
                if isinstance(self.last_accessed, datetime)
                else self.last_accessed
            ),
            "user_id": self.user_id,
            "keywords": self.keywords,
            "emotion_pleasure": self.emotion.pleasure if self.emotion else None,
            "emotion_arousal": self.emotion.arousal if self.emotion else None,
            "emotion_dominance": self.emotion.dominance if self.emotion else None,
            "id": self.id if self.id else None,
        }


@dataclass
class CognitiveMemory(Memory):
    """
    Represents a cognitive memory in Luna's memory system.
    """

    memory_type: str = "cognitive"
    is_private: bool = True
    thought_type: Optional[str] = None

    def to_document(self) -> Dict[str, Any]:
        doc = super().to_document()

        doc.update(
            {
                "is_private": self.is_private,
                "thought_type": self.thought_type,
            }
        )

        return doc


@dataclass
class EpisodicMemory(Memory):
    """
    Represents an episodic memory in Luna's memory system.
    """

    memory_type: str = "episodic"
    participants: List[str] = field(default_factory=list)
    context: str = ""

    def to_document(self) -> Dict[str, Any]:
        doc = super().to_document()

        doc.update(
            {
                "participants": self.participants,
                "context": self.context,
            }
        )

        return doc


@dataclass
class SemanticMemory(Memory):
    """
    Represents a semantic memory in Luna's memory system.
    """

    memory_type: str = "semantic"
    certainty: float = 0.5
    verifiability: float = 0.5
    domain: str = ""
    source: str = ""
    source_reliability: float = 0.5

    def to_document(self) -> Dict[str, Any]:
        doc = super().to_document()

        doc.update(
            {
                "certainty": self.certainty,
                "verifiability": self.verifiability,
                "domain": self.domain,
                "source": self.source,
                "source_reliability": self.source_reliability,
            }
        )

        return doc


@dataclass
class EmotionalMemory(Memory):
    """
    Represents an emotional memory in Luna's memory system.
    """

    memory_type: str = "emotional"
    trigger: str = ""
    event_pleasure: float = 0.5
    event_arousal: float = 0.5
    event_dominance: float = 0.5

    def to_document(self) -> Dict[str, Any]:
        doc = super().to_document()

        doc.update(
            {
                "trigger": self.trigger,
                "event_pleasure": self.event_pleasure,
                "event_arousal": self.event_arousal,
                "event_dominance": self.event_dominance,
            }
        )

        return doc


@dataclass
class RelationshipMemory(Memory):
    """
    Represents a relationship memory in Luna's memory system.
    """

    memory_type: str = "relationship"
    relationship_type: str = ""
    closeness: float = 0.5
    trust: float = 0.5
    apprehension: float = 0.5
    shared_experiences: List[str] = field(default_factory=list)
    connection_points: List[str] = field(default_factory=list)
    inside_references: List[str] = field(default_factory=list)

    def to_document(self) -> Dict[str, Any]:
        doc = super().to_document()

        doc.update(
            {
                "relationship_type": self.relationship_type,
                "closeness": self.closeness,
                "trust": self.trust,
                "apprehension": self.apprehension,
                "shared_experiences": self.shared_experiences,
                "connection_points": self.connection_points,
            }
        )

        return doc


@dataclass
class MemoryQuery:
    """
    Common parameters for memory retrieval queries.

    Attributes:
        query: The search text
        memory_type: Type of memory to search for
        limit: Maximum number of results to return
        importance_threshold: Minimum importance level (1-10)
        user_id: Filter by specific user
    """

    # Query Parameters
    query: Optional[str] = None
    memory_type: Optional[str] = None  # None means search all types
    importance_threshold: Optional[int] = None
    user_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    emotional_state: Optional[EmotionalState] = None
    # Query Settings
    limit: int = 5
    update_access_time: bool = True


@dataclass
class CognitiveMemoryQuery(MemoryQuery):
    """
    Parameters for cognitive memory retrieval queries.
    """

    memory_type: str = "cognitive"
    is_private: Optional[bool] = None
    thought_type: Optional[str] = None


@dataclass
class EpisodicMemoryQuery(MemoryQuery):
    """
    Parameters for episodic memory retrieval queries.
    """

    memory_type: str = "episodic"
    participants: Optional[List[str]] = None
    context: Optional[str] = None


@dataclass
class SemanticMemoryQuery(MemoryQuery):
    """
    Parameters for semantic memory retrieval queries.
    """

    memory_type: str = "semantic"
    certainty_threshold: Optional[float] = None
    verifiability_threshold: Optional[float] = None
    domain: Optional[str] = None
    source: Optional[str] = None
    source_reliability_threshold: Optional[float] = None


@dataclass
class EmotionalMemoryQuery(MemoryQuery):
    """
    Parameters for emotional memory retrieval queries.
    """

    memory_type: str = "emotional"
    trigger: Optional[str] = None
    event_pleasure_threshold: Optional[float] = None
    event_arousal_threshold: Optional[float] = None
    event_dominance_threshold: Optional[float] = None


@dataclass
class RelationshipMemoryQuery(MemoryQuery):
    """
    Parameters for relationship memory retrieval queries.
    """

    memory_type: str = "relationship"
    relationship_type: Optional[str] = None
    closeness_threshold: Optional[float] = None
    trust_threshold: Optional[float] = None
    apprehension_threshold: Optional[float] = None
    shared_experiences: Optional[List[str]] = None
    connection_points: Optional[List[str]] = None
    inside_references: Optional[List[str]] = None


@dataclass
class MemoryResult:
    """
    Result from a memory query, containing matching memories.

    Attributes:
        memories: List of matching Memory objects
        query: The original search query
        total_found: Total number of matching memories
        message: Optional status message
    """

    memories: List[
        Memory
        | CognitiveMemory
        | EpisodicMemory
        | EmotionalMemory
        | SemanticMemory
        | RelationshipMemory
    ]
    query: str
    total_found: int
    message: Optional[str] = None
    scores: Dict[str, float] = field(default_factory=dict)

    def __iter__(
        self,
    ) -> Generator[
        Memory
        | CognitiveMemory
        | EpisodicMemory
        | EmotionalMemory
        | SemanticMemory
        | RelationshipMemory,
        None,
        None,
    ]:
        """
        Support for the 'in' operator to iterate over memories.

        Returns:
            bool: True if the tool exists in the registry, False otherwise
        """
        for memory in self.memories:
            yield memory
