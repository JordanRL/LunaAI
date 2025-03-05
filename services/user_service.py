"""
User service interface for Luna.

This module defines the interface for user management.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from domain.models.user import UserProfile, UserRelationship, RelationshipUpdateRequest

class UserService(ABC):
    """
    Interface for user management.
    
    This service manages user profiles, relationships, and user-related data.
    """
    
    @abstractmethod
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserProfile: User profile or None if not found
        """
        pass
    
    @abstractmethod
    def create_or_get_user(self, user_id: str) -> Tuple[bool, UserProfile, Optional[Dict[str, Any]]]:
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
        pass
    
    @abstractmethod
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Update a user profile.
        
        Args:
            user_id: User identifier
            updates: Dictionary of fields to update
            
        Returns:
            UserProfile: Updated user profile or None if update failed
        """
        pass
    
    @abstractmethod
    def update_user_relationship(self, request: RelationshipUpdateRequest) -> Optional[UserRelationship]:
        """
        Update a user relationship.
        
        Args:
            request: Relationship update request
            
        Returns:
            UserRelationship: Updated relationship or None if update failed
        """
        pass
    
    @abstractmethod
    def update_interaction_stats(self, user_id: str, increment: int = 1) -> bool:
        """
        Update interaction statistics for a user.
        
        Args:
            user_id: User identifier
            increment: Amount to increment interaction count
            
        Returns:
            bool: Whether the update was successful
        """
        pass
    
    @abstractmethod
    def save_user_data(self, user_id: str) -> bool:
        """
        Save all user data to persistent storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: Whether the save was successful
        """
        pass