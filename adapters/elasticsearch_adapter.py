from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union, Tuple
from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch
from domain.models.config import LunaMemoriesIndexSchema, UserProfileIndexSchema, UserRelationshipIndexSchema
from domain.models.memory import Memory
from domain.models.user import UserProfile, UserRelationship


class ElasticsearchAdapter:
    """
    Adapter class for interacting with Elasticsearch storage for Luna's memory and user data systems.
    Handles memory storage, user profiles, relationships, and index management operations.
    """
    DEFAULT_HOST = "http://localhost:9200"
    DEFAULT_MEMORY_INDEX = "luna-memories"
    DEFAULT_USER_PROFILE_INDEX = "luna-user-profiles"
    DEFAULT_USER_RELATIONSHIP_INDEX = "luna-user-relationships"
    IGNORED_STATUS_CODES = [400, 404]

    def __init__(
            self,
            host: str = DEFAULT_HOST,
            memory_index_name: str = DEFAULT_MEMORY_INDEX,
            user_profile_index_name: str = DEFAULT_USER_PROFILE_INDEX,
            user_relationship_index_name: str = DEFAULT_USER_RELATIONSHIP_INDEX,
            rebuild_indices: bool = False
    ) -> None:
        """
        Initialize the Elasticsearch adapter.

        Args:
            host: Elasticsearch host URL
            memory_index_name: Name of the memory index to use
            user_profile_index_name: Name of the user profile index to use
            user_relationship_index_name: Name of the user relationship index to use
            rebuild_indices: Whether to rebuild the indices on startup

        Raises:
            ConnectionError: If unable to connect to Elasticsearch
        """
        self.memory_index_name = memory_index_name
        self.user_profile_index_name = user_profile_index_name
        self.user_relationship_index_name = user_relationship_index_name
        
        try:
            self.es = Elasticsearch(hosts=host)
            if not self.es.ping():
                raise ConnectionError("Elasticsearch connection failed.")

            if rebuild_indices:
                self._initialize_indices()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Elasticsearch: {str(e)}")

    def _initialize_indices(self) -> None:
        """
        Initialize or rebuild all Elasticsearch indices with proper mappings and settings.
        """
        # Initialize memory index
        try:
            self._initialize_memory_index()
            self._initialize_user_profile_index()
            self._initialize_user_relationship_index()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize indices: {str(e)}")

    def _initialize_memory_index(self) -> None:
        """
        Initialize or rebuild the memory index.
        """
        try:
            self.es.indices.delete(
                index=self.memory_index_name,
                ignore=self.IGNORED_STATUS_CODES
            )
            self.es.indices.create(
                index=self.memory_index_name,
                body={
                    "mappings": LunaMemoriesIndexSchema.mappings,
                    "settings": LunaMemoriesIndexSchema.settings
                }
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize memory index: {str(e)}")

    def _initialize_user_profile_index(self) -> None:
        """
        Initialize or rebuild the user profile index.
        """
        try:
            self.es.indices.delete(
                index=self.user_profile_index_name,
                ignore=self.IGNORED_STATUS_CODES
            )
            self.es.indices.create(
                index=self.user_profile_index_name,
                body={
                    "mappings": UserProfileIndexSchema.mappings,
                    "settings": UserProfileIndexSchema.settings
                }
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize user profile index: {str(e)}")

    def _initialize_user_relationship_index(self) -> None:
        """
        Initialize or rebuild the user relationship index.
        """
        try:
            self.es.indices.delete(
                index=self.user_relationship_index_name,
                ignore=self.IGNORED_STATUS_CODES
            )
            self.es.indices.create(
                index=self.user_relationship_index_name,
                body={
                    "mappings": UserRelationshipIndexSchema.mappings,
                    "settings": UserRelationshipIndexSchema.settings
                }
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize user relationship index: {str(e)}")

    # Memory-related methods
    def store_memory(self, memory: Memory) -> Optional[Dict[str, Any]]:
        """
        Store a memory in Elasticsearch.

        Args:
            memory: Memory object to store

        Returns:
            Dict containing the response from Elasticsearch or None if operation failed

        Raises:
            Exception: If storage operation fails
        """
        try:
            doc = memory.to_document()
            response = self.es.index(index=self.memory_index_name, body=doc)
            return response.body
        except Exception as e:
            raise Exception(f"Failed to store memory: {str(e)}")
    
    # User Profile methods
    def store_user_profile(self, profile: UserProfile) -> Optional[Dict[str, Any]]:
        """
        Store a user profile in Elasticsearch.

        Args:
            profile: UserProfile object to store

        Returns:
            Dict containing the response from Elasticsearch or None if operation failed

        Raises:
            Exception: If storage operation fails
        """
        try:
            # Convert UserProfile to dictionary for Elasticsearch
            doc = profile.model_dump()
            doc["doc_type"] = "profile"  # Mark document type
            
            # Use user_id as document ID for easy retrieval
            response = self.es.index(
                index=self.user_profile_index_name, 
                id=profile.user_id,
                body=doc
            )
            return response.body
        except Exception as e:
            raise Exception(f"Failed to store user profile: {str(e)}")
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieve a user profile from Elasticsearch.

        Args:
            user_id: User ID to retrieve

        Returns:
            UserProfile object or None if not found

        Raises:
            Exception: If retrieval operation fails
        """
        try:
            response = self.es.get(
                index=self.user_profile_index_name,
                id=user_id,
                ignore=self.IGNORED_STATUS_CODES
            )
            
            if response.status_code == 404:
                return None
                
            # Convert Elasticsearch document back to UserProfile
            source = response.body["_source"]
            return UserProfile.model_validate(source)
        except Exception as e:
            raise Exception(f"Failed to retrieve user profile: {str(e)}")
    
    # User Relationship methods
    def store_user_relationship(self, relationship: UserRelationship) -> Optional[Dict[str, Any]]:
        """
        Store a user relationship in Elasticsearch.

        Args:
            relationship: UserRelationship object to store

        Returns:
            Dict containing the response from Elasticsearch or None if operation failed

        Raises:
            Exception: If storage operation fails
        """
        try:
            # Convert UserRelationship to dictionary for Elasticsearch
            doc = relationship.model_dump()
            doc["doc_type"] = "relationship"  # Mark document type
            
            # Use user_id as document ID for easy retrieval
            response = self.es.index(
                index=self.user_relationship_index_name, 
                id=relationship.user_id,
                body=doc
            )
            return response.body
        except Exception as e:
            raise Exception(f"Failed to store user relationship: {str(e)}")
    
    def get_user_relationship(self, user_id: str) -> Optional[UserRelationship]:
        """
        Retrieve a user relationship from Elasticsearch.

        Args:
            user_id: User ID to retrieve

        Returns:
            UserRelationship object or None if not found

        Raises:
            Exception: If retrieval operation fails
        """
        try:
            response = self.es.get(
                index=self.user_relationship_index_name,
                id=user_id,
                ignore=self.IGNORED_STATUS_CODES
            )
            
            if response.status_code == 404:
                return None
                
            # Convert Elasticsearch document back to UserRelationship
            source = response.body["_source"]
            return UserRelationship.model_validate(source)
        except Exception as e:
            raise Exception(f"Failed to retrieve user relationship: {str(e)}")
    
    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the system.

        Args:
            user_id: User ID to check

        Returns:
            bool: True if the user exists, False otherwise
        """
        try:
            response = self.es.exists(
                index=self.user_profile_index_name,
                id=user_id
            )
            return response.body
        except Exception:
            return False
    
    def update_user_profile_field(self, user_id: str, field_path: str, value: Any) -> bool:
        """
        Update a specific field in a user profile.

        Args:
            user_id: User ID to update
            field_path: Path to the field to update (e.g., "biographical.name")
            value: New value for the field

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            response = self.es.update(
                index=self.user_profile_index_name,
                id=user_id,
                body={
                    "doc": {field_path: value}
                }
            )
            return response.status_code in [200, 201]
        except Exception:
            return False
    
    def update_user_relationship_field(self, user_id: str, field_path: str, value: Any) -> bool:
        """
        Update a specific field in a user relationship.

        Args:
            user_id: User ID to update
            field_path: Path to the field to update (e.g., "emotional_dynamics.trust_level")
            value: New value for the field

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            response = self.es.update(
                index=self.user_relationship_index_name,
                id=user_id,
                body={
                    "doc": {field_path: value}
                }
            )
            return response.status_code in [200, 201]
        except Exception:
            return False
