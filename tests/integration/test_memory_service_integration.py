"""
Integration tests for the MemoryService with a real Elasticsearch instance.

These tests will create actual data in Elasticsearch and clean up afterward.
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta

import pytest
from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exceptions

# Add project root to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from adapters.elasticsearch_adapter import ElasticsearchAdapter
from domain.models.emotion import EmotionalState
from domain.models.memory import (
    EmotionalMemory,
    EmotionalMemoryQuery,
    EpisodicMemory,
    EpisodicMemoryQuery,
    Memory,
    MemoryQuery,
    RelationshipMemory,
    RelationshipMemoryQuery,
    SemanticMemory,
    SemanticMemoryQuery,
)
from services.memory_service import MemoryService


# Skip all tests in this class if Elasticsearch is not available
def check_elasticsearch():
    try:
        es = Elasticsearch(hosts="http://localhost:9200", request_timeout=2)
        return es.ping()
    except Exception:
        return False


# Decorator to skip all tests if Elasticsearch is not available
elasticsearch_required = pytest.mark.skipif(
    not check_elasticsearch(), reason="Elasticsearch is not available at http://localhost:9200"
)


@elasticsearch_required
class TestMemoryServiceIntegration(unittest.TestCase):
    """
    Integration tests for the MemoryService class with real Elasticsearch.

    These tests require an Elasticsearch instance running at http://localhost:9200.
    """

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Use test-specific indices to avoid interfering with real data
        cls.test_memory_index = "test-luna-memories"
        cls.test_profile_index = "test-luna-user-profiles"
        cls.test_relationship_index = "test-luna-user-relationships"
        print("Elasticsearch available - integration tests will run")

    def setUp(self):
        """Set up test fixtures."""
        # Create a real ElasticsearchAdapter with test indices
        self.es_adapter = ElasticsearchAdapter(
            memory_index_name=self.test_memory_index,
            user_profile_index_name=self.test_profile_index,
            user_relationship_index_name=self.test_relationship_index,
            rebuild_indices=True,  # This will create fresh indices for each test run
        )

        # Create memory service with real adapter
        self.memory_service = MemoryService(self.es_adapter)

        # Wait a moment for indices to be created
        time.sleep(1)

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test indices using the adapter methods
        try:
            self.es_adapter.delete_index(self.test_memory_index)
            self.es_adapter.delete_index(self.test_profile_index)
            self.es_adapter.delete_index(self.test_relationship_index)
        except Exception as e:
            print(f"Warning: Failed to clean up test indices: {str(e)}")

        # Wait a moment for indices to be deleted
        time.sleep(1)

    def test_store_and_retrieve_episodic_memory(self):
        """Test storing and retrieving an episodic memory."""
        # Create test memory
        memory = EpisodicMemory(
            content="Had a productive meeting with the team",
            participants=["Jordan", "Taylor", "Alex"],
            context="Weekly project sync",
            importance=8,
            keywords=["meeting", "project", "teamwork"],
        )

        # Store the memory
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Retrieve by ID
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, memory.content)
        self.assertEqual(retrieved.participants, memory.participants)
        self.assertEqual(retrieved.memory_type, "episodic")

        # Retrieve by query
        query = EpisodicMemoryQuery(query="meeting", participants=["Jordan"])
        result = self.memory_service.retrieve_memories(query)
        self.assertEqual(result.total_found, 1)
        self.assertEqual(len(result.memories), 1)
        self.assertEqual(result.memories[0].content, memory.content)

    def test_store_and_retrieve_semantic_memory(self):
        """Test storing and retrieving a semantic memory."""
        # Create test memory
        memory = SemanticMemory(
            content="Python is a high-level programming language",
            domain="computer science",
            certainty=0.95,
            verifiability=0.9,
            source="professional experience",
            source_reliability=0.95,
            importance=7,
            keywords=["python", "programming", "language"],
        )

        # Store the memory
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Retrieve by ID
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, memory.content)
        self.assertEqual(retrieved.memory_type, "semantic")
        self.assertEqual(retrieved.domain, memory.domain)
        self.assertAlmostEqual(retrieved.certainty, memory.certainty)

        # Retrieve by query
        query = SemanticMemoryQuery(
            query="programming", domain="computer science", certainty_threshold=0.9
        )
        result = self.memory_service.retrieve_memories(query)
        self.assertEqual(result.total_found, 1)
        self.assertEqual(len(result.memories), 1)
        self.assertEqual(result.memories[0].content, memory.content)

    def test_store_and_retrieve_emotional_memory(self):
        """Test storing and retrieving an emotional memory."""
        # Create test memory with emotional state
        emotion = EmotionalState(pleasure=0.8, arousal=0.7, dominance=0.6)
        memory = EmotionalMemory(
            content="Felt proud after completing a difficult project",
            trigger="project completion",
            event_pleasure=0.9,
            event_arousal=0.8,
            event_dominance=0.7,
            emotion=emotion,
            importance=8,
            keywords=["pride", "accomplishment", "project"],
        )

        # Store the memory
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Retrieve by ID
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, memory.content)
        self.assertEqual(retrieved.memory_type, "emotional")
        self.assertEqual(retrieved.trigger, memory.trigger)
        self.assertAlmostEqual(retrieved.event_pleasure, memory.event_pleasure)
        self.assertIsNotNone(retrieved.emotion)
        self.assertAlmostEqual(retrieved.emotion.pleasure, emotion.pleasure)

        # Retrieve by query
        query = EmotionalMemoryQuery(query="proud", trigger="project", event_pleasure_threshold=0.8)
        result = self.memory_service.retrieve_memories(query)
        self.assertEqual(result.total_found, 1)
        self.assertEqual(len(result.memories), 1)
        self.assertEqual(result.memories[0].content, memory.content)

        # Test emotional state matching
        query_emotion = EmotionalMemoryQuery(
            query="", emotional_state=EmotionalState(pleasure=0.7, arousal=0.6, dominance=0.5)
        )
        result = self.memory_service.retrieve_memories(query_emotion)
        self.assertEqual(result.total_found, 1)

    def test_store_and_retrieve_relationship_memory(self):
        """Test storing and retrieving a relationship memory."""
        # Create test memory
        memory = RelationshipMemory(
            content="Built trust with Jordan through successful project collaboration",
            relationship_type="professional",
            closeness=0.8,
            trust=0.9,
            apprehension=0.2,
            shared_experiences=["project collaboration", "problem solving"],
            connection_points=["technology", "innovation"],
            importance=9,
            keywords=["trust", "collaboration", "professional"],
        )

        # Store the memory
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Retrieve by ID
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, memory.content)
        self.assertEqual(retrieved.memory_type, "relationship")
        self.assertEqual(retrieved.relationship_type, memory.relationship_type)
        self.assertAlmostEqual(retrieved.trust, memory.trust)

        # Retrieve by query
        query = RelationshipMemoryQuery(
            query="trust", relationship_type="professional", trust_threshold=0.8
        )
        result = self.memory_service.retrieve_memories(query)
        self.assertEqual(result.total_found, 1)
        self.assertEqual(len(result.memories), 1)
        self.assertEqual(result.memories[0].content, memory.content)

    def test_update_memory(self):
        """Test updating a memory."""
        # Create and store a memory
        memory = EpisodicMemory(
            content="Initial memory content",
            participants=["Jordan"],
            context="Initial context",
            importance=5,
        )
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Update the memory
        updates = {
            "content": "Updated memory content",
            "importance": 8,
            "keywords": ["updated", "memory"],
        }
        result = self.memory_service.update_memory(memory_id, updates)
        self.assertTrue(result)

        # Wait for Elasticsearch to update
        time.sleep(1)

        # Retrieve and verify the update
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertEqual(retrieved.content, "Updated memory content")
        self.assertEqual(retrieved.importance, 8)
        self.assertEqual(retrieved.keywords, ["updated", "memory"])
        # Original fields should be preserved
        self.assertEqual(retrieved.participants, ["Jordan"])
        self.assertEqual(retrieved.context, "Initial context")

    def test_delete_memory(self):
        """Test deleting a memory."""
        # Create and store a memory
        memory = EpisodicMemory(content="Memory to be deleted", importance=3)
        memory_id = self.memory_service.store_memory(memory)
        self.assertIsNotNone(memory_id)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Verify it exists
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNotNone(retrieved)

        # Delete the memory
        result = self.memory_service.delete_memory(memory_id)
        self.assertTrue(result)

        # Wait for Elasticsearch to delete
        time.sleep(1)

        # Verify it's gone
        retrieved = self.memory_service.get_memory_by_id(memory_id)
        self.assertIsNone(retrieved)

    def test_memory_importance_sorting(self):
        """Test that memories are returned sorted by importance."""
        # Create and store memories with different importance
        low_memory = EpisodicMemory(
            content="Low importance memory", importance=3, keywords=["test", "sorting"]
        )
        mid_memory = EpisodicMemory(
            content="Medium importance memory", importance=5, keywords=["test", "sorting"]
        )
        high_memory = EpisodicMemory(
            content="High importance memory", importance=9, keywords=["test", "sorting"]
        )

        # Store memories
        low_id = self.memory_service.store_memory(low_memory)
        mid_id = self.memory_service.store_memory(mid_memory)
        high_id = self.memory_service.store_memory(high_memory)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Query memories
        query = MemoryQuery(query="test sorting", limit=10)
        result = self.memory_service.retrieve_memories(query)

        # Verify order by importance
        self.assertEqual(len(result.memories), 3)
        self.assertEqual(result.memories[0].content, "High importance memory")
        self.assertEqual(result.memories[1].content, "Medium importance memory")
        self.assertEqual(result.memories[2].content, "Low importance memory")

    def test_memory_caching(self):
        """Test that memory caching works."""
        # Create and store a memory
        memory = EpisodicMemory(content="Memory for cache testing", importance=7)
        memory_id = self.memory_service.store_memory(memory)

        # Wait for Elasticsearch to index
        time.sleep(1)

        # Get the memory to cache it
        _ = self.memory_service.get_memory_by_id(memory_id)

        # Mock the es_adapter.get_memory method to track calls
        original_get_memory = self.es_adapter.get_memory
        call_count = [0]

        def mock_get_memory(*args, **kwargs):
            call_count[0] += 1
            return original_get_memory(*args, **kwargs)

        self.es_adapter.get_memory = mock_get_memory

        # Get the memory again - should be from cache
        _ = self.memory_service.get_memory_by_id(memory_id)

        # Should not have called Elasticsearch
        self.assertEqual(call_count[0], 0)

        # Restore original method
        self.es_adapter.get_memory = original_get_memory


if __name__ == "__main__":
    unittest.main()
