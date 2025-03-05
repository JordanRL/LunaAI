"""
Memory service interface for Luna.

This module defines the interface for memory storage and retrieval.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from domain.models.memory import Memory, MemoryQuery, MemoryResult

class MemoryService(ABC):
    """
    Interface for memory storage and retrieval.
    
    This service manages storing and retrieving memories from persistent storage.
    """
    
    @abstractmethod
    def store_memory(self, memory: Memory) -> str:
        """
        Store a memory and return its ID.
        
        Args:
            memory: The memory to store
            
        Returns:
            str: ID of the stored memory
        """
        pass
    
    @abstractmethod
    def retrieve_memories(self, query: MemoryQuery) -> MemoryResult:
        """
        Retrieve memories based on a query.
        
        Args:
            query: Parameters for the memory query
            
        Returns:
            MemoryResult: Results of the query
        """
        pass
    
    @abstractmethod
    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory: The retrieved memory, or None if not found
        """
        pass
    
    @abstractmethod
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory's metadata.
        
        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: Whether the update was successful
        """
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: Whether the deletion was successful
        """
        pass