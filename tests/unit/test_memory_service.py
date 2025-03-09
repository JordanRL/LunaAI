"""
Unit tests for the MemoryService.
"""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

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
from services.memory_service import MemoryService


class TestMemoryService(unittest.TestCase):
    """Tests for the MemoryService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock ElasticsearchAdapter
        self.mock_es_adapter = MagicMock(spec=ElasticsearchAdapter)
        self.mock_es_adapter.memory_index_name = "test-memories"

        # Create mock Elasticsearch instance and client returned by options()
        self.mock_options_client = MagicMock()
        self.mock_es = MagicMock()
        self.mock_es.options.return_value = self.mock_options_client
        self.mock_es_adapter.es = self.mock_es

        # Create memory service with mock adapter
        self.memory_service = MemoryService(self.mock_es_adapter)

    def test_store_memory(self):
        """Test storing a memory."""
        # Create test memory
        memory = EpisodicMemory(
            content="Met Jordan for coffee",
            participants=["Jordan"],
            context="Coffee shop",
            importance=7,
        )

        # Set up mock response
        mock_response = {"_id": "test123", "result": "created"}
        self.mock_es_adapter.store_memory.return_value = mock_response

        # Call method
        result = self.memory_service.store_memory(memory)

        # Verify results
        self.assertEqual(result, "test123")
        self.mock_es_adapter.store_memory.assert_called_once_with(memory)

        # Check cache updated
        self.assertIn("test123", self.memory_service._memory_cache)
        cached_memory, _ = self.memory_service._memory_cache["test123"]
        self.assertEqual(cached_memory, memory)

    def test_retrieve_memories(self):
        """Test retrieving memories with a query."""
        # Create test query
        query = EpisodicMemoryQuery(query="coffee", participants=["Jordan"])

        # Set up mock search response
        mock_response = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 1.5,
                        "_source": {
                            "id": "test123",
                            "content": "Met Jordan for coffee",
                            "memory_type": "episodic",
                            "participants": ["Jordan"],
                            "context": "Coffee shop",
                            "importance": 7,
                            "timestamp": datetime.now().isoformat(),
                            "keywords": ["coffee", "meeting"],
                        },
                    }
                ],
            }
        }
        # Use the adapter's search method instead of direct ES access
        self.mock_es_adapter.search.return_value = mock_response

        # Mock check_document_exists for access time updates
        self.mock_es_adapter.check_document_exists.return_value = True

        # Call method
        result = self.memory_service.retrieve_memories(query)

        # Verify results
        self.assertIsInstance(result, MemoryResult)
        self.assertEqual(len(result.memories), 1)
        self.assertEqual(result.total_found, 1)
        self.assertEqual(result.memories[0].content, "Met Jordan for coffee")
        self.assertEqual(result.memories[0].memory_type, "episodic")
        self.assertEqual(result.scores[result.memories[0].id], 1.5)

        # Verify search query
        self.mock_es_adapter.search.assert_called_once()
        args, kwargs = self.mock_es_adapter.search.call_args
        self.assertEqual(kwargs["index_name"], "test-memories")
        self.assertIn("query", kwargs)

        # Verify update access time was called
        self.mock_es_adapter.update_document.assert_called()

        # Test error case for search
        self.mock_es_adapter.search.reset_mock()
        self.mock_es_adapter.update_document.reset_mock()
        self.mock_es_adapter.check_document_exists.reset_mock()

        # Set up mock search response for error
        self.mock_es_adapter.search.side_effect = Exception("Search error")

        # Call method
        result = self.memory_service.retrieve_memories(query)

        # Verify error handling
        self.assertIsInstance(result, MemoryResult)
        self.assertEqual(len(result.memories), 0)
        self.assertEqual(result.total_found, 0)
        self.assertIn("Error", result.message)

        # Verify update access time was not called
        self.mock_es_adapter.update_document.assert_not_called()

        # Reset for next test
        self.mock_es_adapter.search.side_effect = None

    def test_get_memory_by_id(self):
        """Test retrieving a memory by ID."""
        # Set up mock get response
        mock_response = {
            "_id": "test123",
            "found": True,
            "_source": {
                "id": "test123",
                "content": "Met Jordan for coffee",
                "memory_type": "episodic",
                "participants": ["Jordan"],
                "context": "Coffee shop",
                "importance": 7,
                "timestamp": datetime.now().isoformat(),
                "keywords": ["coffee", "meeting"],
            },
        }
        # Use the adapter's get_memory method instead of direct ES access
        self.mock_es_adapter.get_memory.return_value = mock_response

        # Mock the check_document_exists for update_memory_access_time
        self.mock_es_adapter.check_document_exists.return_value = True

        # Call method
        memory = self.memory_service.get_memory_by_id("test123")

        # Verify results
        self.assertIsNotNone(memory)
        self.assertEqual(memory.content, "Met Jordan for coffee")
        self.assertEqual(memory.memory_type, "episodic")
        self.assertEqual(memory.participants, ["Jordan"])

        # Verify get_memory was called
        self.mock_es_adapter.get_memory.assert_called_once_with("test123")

        # Verify update access time was called
        self.mock_es_adapter.update_document.assert_called()

        # Test caching behavior
        self.mock_es_adapter.get_memory.reset_mock()
        self.mock_es_adapter.update_document.reset_mock()

        # Get same memory again
        memory2 = self.memory_service.get_memory_by_id("test123")

        # Verify ES get_memory was NOT called (cached)
        self.mock_es_adapter.get_memory.assert_not_called()

        # But update access time should still be called
        self.mock_es_adapter.update_document.assert_called()

        # Test memory not found case
        self.mock_es_adapter.get_memory.reset_mock()
        self.mock_es_adapter.update_document.reset_mock()

        # Set up mock get response for memory not found
        self.mock_es_adapter.get_memory.return_value = {"found": False}

        # Call method
        memory = self.memory_service.get_memory_by_id("nonexistent")

        # Verify result is None
        self.assertIsNone(memory)

        # Verify update access time was not called
        self.mock_es_adapter.update_document.assert_not_called()

        # Test error case
        self.mock_es_adapter.get_memory.reset_mock()

        # We need to clear the cache first, otherwise it will return the cached memory
        self.memory_service._memory_cache.clear()

        self.mock_es_adapter.get_memory.side_effect = Exception("Get memory error")

        # Call method
        memory = self.memory_service.get_memory_by_id("test123")

        # Verify result is None
        self.assertIsNone(memory)

        # Reset for next test
        self.mock_es_adapter.get_memory.side_effect = None

    def test_update_memory(self):
        """Test updating a memory."""
        # Set update_memory to return True
        self.mock_es_adapter.update_memory.return_value = True

        # Call method
        result = self.memory_service.update_memory("test123", {"importance": 8})

        # Verify results
        self.assertTrue(result)

        # Verify update_memory was called with correct parameters
        self.mock_es_adapter.update_memory.assert_called_once_with("test123", {"importance": 8})

        # Add to cache then update
        memory = EpisodicMemory(content="Test memory", id="test123")
        self.memory_service._memory_cache["test123"] = (memory, datetime.now())

        # Update again
        result = self.memory_service.update_memory("test123", {"importance": 9})

        # Cache should be invalidated
        self.assertNotIn("test123", self.memory_service._memory_cache)

    def test_delete_memory(self):
        """Test deleting a memory."""
        # Set delete_memory to return True
        self.mock_es_adapter.delete_memory.return_value = True

        # Add to cache
        memory = EpisodicMemory(content="Test memory", id="test123")
        self.memory_service._memory_cache["test123"] = (memory, datetime.now())

        # Call method
        result = self.memory_service.delete_memory("test123")

        # Verify results
        self.assertTrue(result)

        # Verify delete_memory was called with correct parameters
        self.mock_es_adapter.delete_memory.assert_called_once_with("test123")

        # Cache should be invalidated
        self.assertNotIn("test123", self.memory_service._memory_cache)

        # Test delete failure case
        self.mock_es_adapter.delete_memory.reset_mock()
        self.mock_es_adapter.delete_memory.return_value = False

        # Add back to cache
        self.memory_service._memory_cache["test123"] = (memory, datetime.now())

        # Call method
        result = self.memory_service.delete_memory("test123")

        # Verify results
        self.assertFalse(result)

        # Cache should still be invalidated
        self.assertNotIn("test123", self.memory_service._memory_cache)

        # Test error case
        self.mock_es_adapter.delete_memory.reset_mock()
        self.mock_es_adapter.delete_memory.side_effect = Exception("Delete error")

        # Call method
        result = self.memory_service.delete_memory("test123")

        # Verify results
        self.assertFalse(result)

        # Reset for next test
        self.mock_es_adapter.delete_memory.side_effect = None

    def test_update_memory_access_time(self):
        """Test updating memory access time."""
        # Setup - document exists
        self.mock_es_adapter.check_document_exists.return_value = True
        memory_id = "test123"

        # Call method - since this function returns None, we'll test its effects instead
        self.memory_service._update_memory_access_time(memory_id)

        # Verify update_document was called
        self.mock_es_adapter.update_document.assert_called_once()
        args, kwargs = self.mock_es_adapter.update_document.call_args
        self.assertEqual(kwargs["index_name"], "test-memories")
        self.assertEqual(kwargs["doc_id"], memory_id)

        # Test document does not exist
        self.mock_es_adapter.update_document.reset_mock()
        self.mock_es_adapter.check_document_exists.return_value = False

        # Call method
        self.memory_service._update_memory_access_time(memory_id)

        # Verify update_document was not called
        self.mock_es_adapter.update_document.assert_not_called()

        # Test error case
        self.mock_es_adapter.check_document_exists.side_effect = Exception("Check error")

        # Call method (should not raise exception)
        try:
            self.memory_service._update_memory_access_time(memory_id)
            exception_raised = False
        except Exception:
            exception_raised = True

        # Verify no exception was raised
        self.assertFalse(exception_raised)

        # Reset for next test
        self.mock_es_adapter.check_document_exists.side_effect = None

    def test_memory_type_conversion(self):
        """Test converting documents to specific memory types."""
        # Test episodic memory
        episodic_doc = {
            "id": "ep1",
            "content": "Met with friends",
            "memory_type": "episodic",
            "participants": ["Alex", "Taylor"],
            "context": "Restaurant",
            "importance": 6,
            "timestamp": datetime.now().isoformat(),
        }
        episodic = self.memory_service._document_to_memory(episodic_doc)
        self.assertIsInstance(episodic, EpisodicMemory)
        self.assertEqual(episodic.participants, ["Alex", "Taylor"])

        # Test semantic memory
        semantic_doc = {
            "id": "sem1",
            "content": "Python is a programming language",
            "memory_type": "semantic",
            "certainty": 0.9,
            "domain": "programming",
            "source": "personal experience",
            "source_reliability": 0.8,
            "importance": 5,
            "timestamp": datetime.now().isoformat(),
        }
        semantic = self.memory_service._document_to_memory(semantic_doc)
        self.assertIsInstance(semantic, SemanticMemory)
        self.assertEqual(semantic.certainty, 0.9)
        self.assertEqual(semantic.domain, "programming")

        # Test emotional memory
        emotional_doc = {
            "id": "em1",
            "content": "Felt happy about completing project",
            "memory_type": "emotional",
            "trigger": "project completion",
            "event_pleasure": 0.8,
            "event_arousal": 0.7,
            "event_dominance": 0.6,
            "importance": 7,
            "timestamp": datetime.now().isoformat(),
        }
        emotional = self.memory_service._document_to_memory(emotional_doc)
        self.assertIsInstance(emotional, EmotionalMemory)
        self.assertEqual(emotional.trigger, "project completion")
        self.assertEqual(emotional.event_pleasure, 0.8)

        # Test relationship memory
        relationship_doc = {
            "id": "rel1",
            "content": "Built trust with Jordan",
            "memory_type": "relationship",
            "relationship_type": "friendship",
            "closeness": 0.7,
            "trust": 0.8,
            "apprehension": 0.2,
            "shared_experiences": ["project collaboration", "coffee meetings"],
            "connection_points": ["technology", "music"],
            "importance": 8,
            "timestamp": datetime.now().isoformat(),
        }
        relationship = self.memory_service._document_to_memory(relationship_doc)
        self.assertIsInstance(relationship, RelationshipMemory)
        self.assertEqual(relationship.relationship_type, "friendship")
        self.assertEqual(relationship.trust, 0.8)
        self.assertEqual(
            relationship.shared_experiences, ["project collaboration", "coffee meetings"]
        )

    def test_build_query(self):
        """Test building Elasticsearch queries from MemoryQuery objects."""
        # Test basic query
        basic_query = MemoryQuery(query="test")
        es_query = self.memory_service._build_es_query(basic_query)
        self.assertIn("query", es_query)
        self.assertIn("bool", es_query["query"])
        self.assertIn("must", es_query["query"]["bool"])

        # Test episodic query
        episodic_query = EpisodicMemoryQuery(
            query="coffee", participants=["Jordan"], context="meeting"
        )
        es_episodic_query = self.memory_service._build_es_query(episodic_query)
        self.assertIn("query", es_episodic_query)
        self.assertIn("bool", es_episodic_query["query"])

        # Test semantic query
        semantic_query = SemanticMemoryQuery(
            query="python", domain="programming", certainty_threshold=0.7
        )
        es_semantic_query = self.memory_service._build_es_query(semantic_query)
        self.assertIn("query", es_semantic_query)
        self.assertIn("bool", es_semantic_query["query"])

        # Test empty query
        empty_query = MemoryQuery(query="")
        es_empty_query = self.memory_service._build_es_query(empty_query)
        self.assertIn("query", es_empty_query)
        self.assertIn("match_all", es_empty_query["query"])

        # Test query with memory_type
        memory_type_query = MemoryQuery(query="test", memory_type="episodic")
        es_memory_type_query = self.memory_service._build_es_query(memory_type_query)
        bool_query = es_memory_type_query["query"]["bool"]
        self.assertTrue(
            any(
                "term" in clause and "memory_type" in clause["term"]
                for clause in bool_query.get("filter", [])
            )
        )

        # Test query with user_id
        user_id_query = MemoryQuery(query="test", user_id="test_user")
        es_user_id_query = self.memory_service._build_es_query(user_id_query)
        bool_query = es_user_id_query["query"]["bool"]
        self.assertTrue(
            any(
                "term" in clause and "user_id" in clause["term"]
                for clause in bool_query.get("filter", [])
            )
        )

        # Test query with importance threshold
        importance_query = MemoryQuery(query="test", importance_threshold=5)
        es_importance_query = self.memory_service._build_es_query(importance_query)
        bool_query = es_importance_query["query"]["bool"]
        self.assertTrue(
            any(
                "range" in clause and "importance" in clause["range"]
                for clause in bool_query.get("filter", [])
            )
        )

        # Test query with keywords
        keywords_query = MemoryQuery(query="test", keywords=["important", "meeting"])
        es_keywords_query = self.memory_service._build_es_query(keywords_query)
        bool_query = es_keywords_query["query"]["bool"]
        self.assertTrue(
            any(
                "match" in clause and "keywords" in clause["match"]
                for clause in bool_query.get("should", [])
            )
        )

        # Test semantic query with complete parameters
        full_semantic_query = SemanticMemoryQuery(
            query="python",
            domain="programming",
            certainty_threshold=0.7,
            verifiability_threshold=0.6,
            source="documentation",
            source_reliability_threshold=0.8,
        )
        es_full_semantic_query = self.memory_service._build_es_query(full_semantic_query)
        bool_query = es_full_semantic_query["query"]["bool"]
        filter_clauses = bool_query.get("filter", [])

        # Check each filter clause exists
        self.assertTrue(any("term" in c and "domain" in c["term"] for c in filter_clauses))
        self.assertTrue(any("term" in c and "source" in c["term"] for c in filter_clauses))
        self.assertTrue(any("range" in c and "certainty" in c["range"] for c in filter_clauses))
        self.assertTrue(any("range" in c and "verifiability" in c["range"] for c in filter_clauses))
        self.assertTrue(
            any("range" in c and "source_reliability" in c["range"] for c in filter_clauses)
        )

    def test_build_emotional_query(self):
        """Test building Elasticsearch queries from EmotionalMemoryQuery objects."""
        # Test emotional query with emotional state
        emotional_state = EmotionalState(pleasure=0.7, arousal=0.6, dominance=0.5)
        emotional_query = MemoryQuery(query="happy moment", emotional_state=emotional_state)

        es_emotional_query = self.memory_service._build_es_query(emotional_query)
        bool_query = es_emotional_query["query"]["bool"]
        filter_clauses = bool_query.get("filter", [])

        # Check that emotional state filters are added
        self.assertTrue(
            any("range" in c and "emotion_pleasure" in c["range"] for c in filter_clauses)
        )
        self.assertTrue(
            any("range" in c and "emotion_arousal" in c["range"] for c in filter_clauses)
        )
        self.assertTrue(
            any("range" in c and "emotion_dominance" in c["range"] for c in filter_clauses)
        )

        # Test EmotionalMemoryQuery with all parameters
        full_emotional_query = EmotionalMemoryQuery(
            query="feeling excited",
            trigger="achievement",
            event_pleasure_threshold=0.7,
            event_arousal_threshold=0.8,
            event_dominance_threshold=0.6,
        )

        es_full_emotional_query = self.memory_service._build_es_query(full_emotional_query)
        bool_query = es_full_emotional_query["query"]["bool"]
        must_clauses = bool_query.get("must", [])
        filter_clauses = bool_query.get("filter", [])

        # Check trigger filter exists
        self.assertTrue(any("match" in c and "trigger" in c["match"] for c in must_clauses))

        # Check emotion threshold filters exist
        self.assertTrue(
            any("range" in c and "event_pleasure" in c["range"] for c in filter_clauses)
        )
        self.assertTrue(any("range" in c and "event_arousal" in c["range"] for c in filter_clauses))
        self.assertTrue(
            any("range" in c and "event_dominance" in c["range"] for c in filter_clauses)
        )

    def test_build_relationship_query(self):
        """Test building Elasticsearch queries from RelationshipMemoryQuery objects."""
        # Test relationship query with all parameters
        relationship_query = RelationshipMemoryQuery(
            query="friendship",
            relationship_type="friendship",
            closeness_threshold=0.7,
            trust_threshold=0.8,
            apprehension_threshold=0.2,
            shared_experiences=["coffee", "projects"],
            connection_points=["technology", "movies"],
        )

        es_relationship_query = self.memory_service._build_es_query(relationship_query)
        bool_query = es_relationship_query["query"]["bool"]
        filter_clauses = bool_query.get("filter", [])
        should_clauses = bool_query.get("should", [])

        # Check relationship type filter exists
        self.assertTrue(
            any("term" in c and "relationship_type" in c["term"] for c in filter_clauses)
        )

        # Check threshold filters exist
        self.assertTrue(any("range" in c and "closeness" in c["range"] for c in filter_clauses))
        self.assertTrue(any("range" in c and "trust" in c["range"] for c in filter_clauses))
        self.assertTrue(any("range" in c and "apprehension" in c["range"] for c in filter_clauses))

        # Check shared experiences and connection points matchers exist
        shared_exp_matches = [
            c for c in should_clauses if "match" in c and "shared_experiences" in c["match"]
        ]
        connection_matches = [
            c for c in should_clauses if "match" in c and "connection_points" in c["match"]
        ]

        self.assertEqual(len(shared_exp_matches), 2)  # One for each shared experience
        self.assertEqual(len(connection_matches), 2)  # One for each connection point


if __name__ == "__main__":
    unittest.main()
