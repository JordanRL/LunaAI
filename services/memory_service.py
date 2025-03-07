"""
Memory service interface for Luna.

This module defines the interface for memory storage and retrieval.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from dateutil.parser import parse as parse_date

from adapters.elasticsearch_adapter import ElasticsearchAdapter
from domain.models.emotion import EmotionalState
from domain.models.memory import (
    EmotionalMemory,
    EmotionalMemoryQuery,
    EpisodicMemory,
    EpisodicMemoryQuery,
    Memory,
    MemoryQuery,
    MemoryResult,
    RelationshipMemory,
    RelationshipMemoryQuery,
    SemanticMemory,
    SemanticMemoryQuery,
)


class MemoryService:
    """
    Interface for memory storage and retrieval.

    This service manages storing and retrieving memories from persistent storage.
    """

    def __init__(self, es_adapter: ElasticsearchAdapter):
        """
        Initialize the memory service with an Elasticsearch adapter.

        Args:
            es_adapter: ElasticsearchAdapter for storage operations
        """
        self.es_adapter = es_adapter
        self._memory_cache = {}  # Simple in-memory cache: memory_id -> (memory, timestamp)
        self._cache_ttl = 300  # Cache TTL in seconds (5 minutes)

    def store_memory(self, memory: Memory) -> str:
        """
        Store a memory and return its ID.

        Args:
            memory: The memory to store

        Returns:
            str: ID of the stored memory
        """
        try:
            response = self.es_adapter.store_memory(memory)
            if response and "_id" in response:
                memory_id = response["_id"]
                # Update cache with the new memory
                self._memory_cache[memory_id] = (memory, datetime.now())
                return memory_id
            return None
        except Exception as e:
            print(f"Error storing memory: {str(e)}")
            return None

    def retrieve_memories(self, query: MemoryQuery) -> MemoryResult:
        """
        Retrieve memories based on a query.

        Args:
            query: Parameters for the memory query

        Returns:
            MemoryResult: Results of the query
        """
        try:
            # Build Elasticsearch query based on the MemoryQuery type
            es_query = self._build_es_query(query)

            # Execute search using the adapter method
            es_query.setdefault("size", query.limit)
            search_response = self.es_adapter.search(
                query=es_query, index_name=self.es_adapter.memory_index_name
            )

            # Process results
            results = self._process_search_results(search_response, query)

            # Update access time if requested
            if query.update_access_time and results.memories:
                for memory in results.memories:
                    if memory.id:
                        self._update_memory_access_time(memory.id)

            return results
        except Exception as e:
            print(f"Error retrieving memories: {str(e)}")
            return MemoryResult(
                memories=[],
                query=query.query,
                total_found=0,
                message=f"Error: {str(e)}",
            )

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Memory: The retrieved memory, or None if not found
        """
        # Check cache first
        if memory_id in self._memory_cache:
            memory, timestamp = self._memory_cache[memory_id]
            # If cache entry is still valid
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                # Update access time
                self._update_memory_access_time(memory_id)
                return memory

        try:
            # Get memory document using the adapter
            response = self.es_adapter.get_memory(memory_id)

            # Check if document was found
            if not response.get("found", False):
                return None

            source = response.get("_source", {})
            memory = self._document_to_memory(source)

            # Update cache
            self._memory_cache[memory_id] = (memory, datetime.now())

            # Update access time
            self._update_memory_access_time(memory_id)

            return memory
        except Exception as e:
            print(f"Error getting memory by ID: {str(e)}")
            return None

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory's metadata.

        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update

        Returns:
            bool: Whether the update was successful
        """
        try:
            # Use the adapter to update the document (returns a boolean)
            result = self.es_adapter.update_memory(memory_id, updates)

            # Update cache if exists
            if memory_id in self._memory_cache:
                # Remove from cache to force re-fetch
                del self._memory_cache[memory_id]

            return result
        except Exception as e:
            print(f"Error updating memory: {str(e)}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            bool: Whether the deletion was successful
        """
        try:
            # Use the adapter to delete the memory (returns a boolean)
            result = self.es_adapter.delete_memory(memory_id)

            # Remove from cache
            if memory_id in self._memory_cache:
                del self._memory_cache[memory_id]

            return result
        except Exception as e:
            print(f"Error deleting memory: {str(e)}")
            return False

    def _update_memory_access_time(self, memory_id: str) -> None:
        """
        Update the last_accessed timestamp for a memory.

        Args:
            memory_id: ID of the memory to update
        """
        try:
            # Only update if the memory exists
            if self.es_adapter.check_document_exists(self.es_adapter.memory_index_name, memory_id):
                # Use the adapter's update method
                self.es_adapter.update_document(
                    index_name=self.es_adapter.memory_index_name,
                    doc_id=memory_id,
                    updates={"last_accessed": datetime.now().isoformat()},
                )
        except Exception as e:
            print(f"Error updating memory access time: {str(e)}")

    def _build_es_query(self, query: MemoryQuery) -> Dict[str, Any]:
        """
        Build an Elasticsearch query from a MemoryQuery object.

        Args:
            query: The query to convert

        Returns:
            Dict: Elasticsearch query body
        """
        # Start with a match_all query
        must_clauses = []
        filter_clauses = []
        should_clauses = []

        # Add text search if provided
        if query.query and query.query.strip():
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query.query,
                        "fields": [
                            "content^3",
                            "keywords^2",
                            "context",
                            "participants",
                            "trigger",
                        ],
                    }
                }
            )

        # Add common filters
        if query.memory_type:
            filter_clauses.append({"term": {"memory_type": query.memory_type}})

        if query.importance_threshold is not None:
            filter_clauses.append({"range": {"importance": {"gte": query.importance_threshold}}})

        if query.user_id:
            filter_clauses.append({"term": {"user_id": query.user_id}})

        if query.keywords:
            for keyword in query.keywords:
                should_clauses.append({"match": {"keywords": keyword}})

        if query.emotional_state:
            # Add emotional state filters based on PAD model
            if query.emotional_state.pleasure is not None:
                filter_clauses.append(
                    {
                        "range": {
                            "emotion_pleasure": {
                                "gte": query.emotional_state.pleasure - 0.3,
                                "lte": query.emotional_state.pleasure + 0.3,
                            }
                        }
                    }
                )

            if query.emotional_state.arousal is not None:
                filter_clauses.append(
                    {
                        "range": {
                            "emotion_arousal": {
                                "gte": query.emotional_state.arousal - 0.3,
                                "lte": query.emotional_state.arousal + 0.3,
                            }
                        }
                    }
                )

            if query.emotional_state.dominance is not None:
                filter_clauses.append(
                    {
                        "range": {
                            "emotion_dominance": {
                                "gte": query.emotional_state.dominance - 0.3,
                                "lte": query.emotional_state.dominance + 0.3,
                            }
                        }
                    }
                )

        # Add specialized filters based on query type
        if isinstance(query, EpisodicMemoryQuery):
            if query.participants:
                for participant in query.participants:
                    should_clauses.append({"match": {"participants": participant}})

            if query.context:
                must_clauses.append({"match": {"context": query.context}})

        elif isinstance(query, SemanticMemoryQuery):
            if query.certainty_threshold is not None:
                filter_clauses.append({"range": {"certainty": {"gte": query.certainty_threshold}}})

            if query.verifiability_threshold is not None:
                filter_clauses.append(
                    {"range": {"verifiability": {"gte": query.verifiability_threshold}}}
                )

            if query.domain:
                filter_clauses.append({"term": {"domain": query.domain}})

            if query.source:
                filter_clauses.append({"term": {"source": query.source}})

            if query.source_reliability_threshold is not None:
                filter_clauses.append(
                    {"range": {"source_reliability": {"gte": query.source_reliability_threshold}}}
                )

        elif isinstance(query, EmotionalMemoryQuery):
            if query.trigger:
                must_clauses.append({"match": {"trigger": query.trigger}})

            if query.event_pleasure_threshold is not None:
                filter_clauses.append(
                    {"range": {"event_pleasure": {"gte": query.event_pleasure_threshold}}}
                )

            if query.event_arousal_threshold is not None:
                filter_clauses.append(
                    {"range": {"event_arousal": {"gte": query.event_arousal_threshold}}}
                )

            if query.event_dominance_threshold is not None:
                filter_clauses.append(
                    {"range": {"event_dominance": {"gte": query.event_dominance_threshold}}}
                )

        elif isinstance(query, RelationshipMemoryQuery):
            if query.relationship_type:
                filter_clauses.append({"term": {"relationship_type": query.relationship_type}})

            if query.closeness_threshold is not None:
                filter_clauses.append({"range": {"closeness": {"gte": query.closeness_threshold}}})

            if query.trust_threshold is not None:
                filter_clauses.append({"range": {"trust": {"gte": query.trust_threshold}}})

            if query.apprehension_threshold is not None:
                filter_clauses.append(
                    {"range": {"apprehension": {"gte": query.apprehension_threshold}}}
                )

            if query.shared_experiences:
                for exp in query.shared_experiences:
                    should_clauses.append({"match": {"shared_experiences": exp}})

            if query.connection_points:
                for point in query.connection_points:
                    should_clauses.append({"match": {"connection_points": point}})

        # Build the query dictionary
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if filter_clauses:
            bool_query["filter"] = filter_clauses
        if should_clauses:
            bool_query["should"] = should_clauses
            if not must_clauses:  # If no must clauses, require at least one should match
                bool_query["minimum_should_match"] = 1

        # If empty query, use match_all
        if not bool_query:
            return {"query": {"match_all": {}}}

        return {
            "query": {"bool": bool_query},
            "sort": [
                {"importance": {"order": "desc"}},
                {"timestamp": {"order": "desc"}},
            ],
        }

    def _process_search_results(self, response: Dict[str, Any], query: MemoryQuery) -> MemoryResult:
        """
        Process Elasticsearch search results into a MemoryResult.

        Args:
            response: Elasticsearch response
            query: The original query

        Returns:
            MemoryResult: Processed results
        """
        # In newer Elasticsearch Python client, response is directly a dict, not an object with body
        hits = response.get("hits", {}).get("hits", [])
        total = response.get("hits", {}).get("total", {})

        if isinstance(total, dict):
            total_count = total.get("value", 0)
        else:
            total_count = total

        memories = []
        scores = {}

        for hit in hits:
            memory = self._document_to_memory(hit["_source"])
            if memory:
                memories.append(memory)
                scores[memory.id] = hit.get("_score", 0)

        return MemoryResult(
            memories=memories, query=query.query, total_found=total_count, scores=scores
        )

    def _document_to_memory(self, doc: Dict[str, Any]) -> Optional[Memory]:
        """
        Convert an Elasticsearch document back to a Memory object.

        Args:
            doc: Elasticsearch document

        Returns:
            Memory: Converted memory object or None if invalid
        """
        try:
            memory_type = doc.get("memory_type", "")

            # Convert string dates to datetime objects
            timestamp = doc.get("timestamp")
            if timestamp and isinstance(timestamp, str):
                try:
                    timestamp = parse_date(timestamp)
                except Exception:
                    timestamp = datetime.now()

            last_accessed = doc.get("last_accessed")
            if last_accessed and isinstance(last_accessed, str):
                try:
                    last_accessed = parse_date(last_accessed)
                except Exception:
                    last_accessed = None

            # Create emotional state if emotion data exists
            emotion = None
            if any(
                key in doc for key in ["emotion_pleasure", "emotion_arousal", "emotion_dominance"]
            ):
                emotion = EmotionalState(
                    pleasure=doc.get("emotion_pleasure"),
                    arousal=doc.get("emotion_arousal"),
                    dominance=doc.get("emotion_dominance"),
                )

            # Common attributes for all memory types
            common_attrs = {
                "content": doc.get("content", ""),
                "memory_type": memory_type,
                "importance": doc.get("importance", 5),
                "timestamp": timestamp,
                "last_accessed": last_accessed,
                "user_id": doc.get("user_id"),
                "keywords": doc.get("keywords", []),
                "id": doc.get("id"),
                "emotion": emotion,
            }

            # Create specific memory type based on the memory_type field
            if memory_type == "episodic":
                return EpisodicMemory(
                    **common_attrs,
                    participants=doc.get("participants", []),
                    context=doc.get("context", ""),
                )
            elif memory_type == "semantic":
                return SemanticMemory(
                    **common_attrs,
                    certainty=doc.get("certainty", 0.5),
                    verifiability=doc.get("verifiability", 0.5),
                    domain=doc.get("domain", ""),
                    source=doc.get("source", ""),
                    source_reliability=doc.get("source_reliability", 0.5),
                )
            elif memory_type == "emotional":
                return EmotionalMemory(
                    **common_attrs,
                    trigger=doc.get("trigger", ""),
                    event_pleasure=doc.get("event_pleasure", 0.5),
                    event_arousal=doc.get("event_arousal", 0.5),
                    event_dominance=doc.get("event_dominance", 0.5),
                )
            elif memory_type == "relationship":
                return RelationshipMemory(
                    **common_attrs,
                    relationship_type=doc.get("relationship_type", ""),
                    closeness=doc.get("closeness", 0.5),
                    trust=doc.get("trust", 0.5),
                    apprehension=doc.get("apprehension", 0.5),
                    shared_experiences=doc.get("shared_experiences", []),
                    connection_points=doc.get("connection_points", []),
                    inside_references=doc.get("inside_references", []),
                )
            else:
                # Default to base Memory class
                return Memory(**common_attrs)
        except Exception as e:
            print(f"Error converting document to memory: {str(e)}")
            return None
