from typing import Any, Dict, Optional

from elasticsearch import Elasticsearch

from domain.models.config import (
    LunaMemoriesIndexSchema,
    UserProfileIndexSchema,
    UserRelationshipIndexSchema,
)
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

    # To be moved after initialization methods

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        memory_index_name: str = DEFAULT_MEMORY_INDEX,
        user_profile_index_name: str = DEFAULT_USER_PROFILE_INDEX,
        user_relationship_index_name: str = DEFAULT_USER_RELATIONSHIP_INDEX,
        rebuild_indices: bool = False,
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
            # For Elasticsearch 8.x, use the main client's options method
            # This is the recommended way to handle ignore_status in Elasticsearch 8.x
            self.es.options(ignore_status=self.IGNORED_STATUS_CODES).indices.delete(
                index=self.memory_index_name
            )
            # Create an instance of the schema
            memory_schema = LunaMemoriesIndexSchema()
            self.es.indices.create(
                index=memory_schema.index_name,
                body={
                    "mappings": memory_schema.mappings,
                    "settings": memory_schema.settings,
                },
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize memory index: {str(e)}")

    def _initialize_user_profile_index(self) -> None:
        """
        Initialize or rebuild the user profile index.
        """
        try:
            # For Elasticsearch 8.x, use the main client's options method
            # This is the recommended way to handle ignore_status in Elasticsearch 8.x
            self.es.options(ignore_status=self.IGNORED_STATUS_CODES).indices.delete(
                index=self.user_profile_index_name
            )
            # Create an instance of the schema
            profile_schema = UserProfileIndexSchema()
            self.es.indices.create(
                index=profile_schema.index_name,
                body={
                    "mappings": profile_schema.mappings,
                    "settings": profile_schema.settings,
                },
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize user profile index: {str(e)}")

    def _initialize_user_relationship_index(self) -> None:
        """
        Initialize or rebuild the user relationship index.
        """
        try:
            # For Elasticsearch 8.x, use the main client's options method
            # This is the recommended way to handle ignore_status in Elasticsearch 8.x
            self.es.options(ignore_status=self.IGNORED_STATUS_CODES).indices.delete(
                index=self.user_relationship_index_name
            )
            # Create an instance of the schema
            relationship_schema = UserRelationshipIndexSchema()
            self.es.indices.create(
                index=relationship_schema.index_name,
                body={
                    "mappings": relationship_schema.mappings,
                    "settings": relationship_schema.settings,
                },
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
            # In Elasticsearch 8.x, response is directly the dict
            return response
        except Exception as e:
            raise Exception(f"Failed to store memory: {str(e)}")

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Dict containing the memory document or None if not found

        Raises:
            Exception: If retrieval operation fails
        """
        try:
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.get(index=self.memory_index_name, id=memory_id)

            # For Elasticsearch 8.x, a 404 will not raise an exception with options(ignore_status=[404])
            # Instead, we need to check if the document was found using the 'found' field
            if not response.get("found", False):
                return None

            return response
        except Exception as e:
            raise Exception(f"Failed to retrieve memory: {str(e)}")

    def search_memories(self, query: Dict[str, Any], size: int = 10) -> Optional[Dict[str, Any]]:
        """
        Search for memories using an Elasticsearch query.

        Args:
            query: Elasticsearch query body
            size: Maximum number of results to return

        Returns:
            Dict containing search results or None if operation failed

        Raises:
            Exception: If search operation fails
        """
        try:
            response = self.es.search(index=self.memory_index_name, body=query, size=size)
            return response.body
        except Exception as e:
            raise Exception(f"Failed to search memories: {str(e)}")

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory document.

        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update

        Returns:
            bool: True if update successful, False otherwise

        Raises:
            Exception: If update operation fails
        """
        try:
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.update(
                index=self.memory_index_name, id=memory_id, body={"doc": updates}
            )

            # Check if response indicates success
            result = response.get("result", None)
            return result in ["updated", "noop"]
        except Exception as e:
            raise Exception(f"Failed to update memory: {str(e)}")

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            Exception: If deletion operation fails
        """
        try:
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.delete(index=self.memory_index_name, id=memory_id)

            # Check if result indicates success
            result = response.get("result", None)
            return result == "deleted"
        except Exception as e:
            raise Exception(f"Failed to delete memory: {str(e)}")

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
                index=self.user_profile_index_name, id=profile.user_id, body=doc
            )
            # In Elasticsearch 8.x, response is directly the dict
            return response
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
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=self.IGNORED_STATUS_CODES)
            response = client.get(index=self.user_profile_index_name, id=user_id)

            # For Elasticsearch 8.x, check the found field
            if not response.get("found", False):
                return None

            # Convert Elasticsearch document back to UserProfile
            source = response["_source"]
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
                body=doc,
            )
            # In Elasticsearch 8.x, response is directly the dict
            return response
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
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=self.IGNORED_STATUS_CODES)
            response = client.get(index=self.user_relationship_index_name, id=user_id)

            # For Elasticsearch 8.x, check the found field
            if not response.get("found", False):
                return None

            # Convert Elasticsearch document back to UserRelationship
            source = response["_source"]
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
            response = self.es.exists(index=self.user_profile_index_name, id=user_id)
            # In Elasticsearch 8.x, response.body for exists() is a boolean
            return response
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
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.update(
                index=self.user_profile_index_name, id=user_id, body={"doc": {field_path: value}}
            )

            # Check if result indicates success
            result = response.get("result", None)
            return result in ["updated", "noop"]
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
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.update(
                index=self.user_relationship_index_name,
                id=user_id,
                body={"doc": {field_path: value}},
            )

            # Check if result indicates success
            result = response.get("result", None)
            return result in ["updated", "noop"]
        except Exception:
            return False

    # Index operations for proper encapsulation
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an Elasticsearch index.

        Args:
            index_name: Name of the index to delete

        Returns:
            bool: True if deletion was successful or index didn't exist, False otherwise
        """
        try:
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=self.IGNORED_STATUS_CODES)
            response = client.indices.delete(index=index_name)

            # Check if the operation was acknowledged
            return response.get("acknowledged", False)
        except Exception as e:
            print(f"Error deleting index {index_name}: {str(e)}")
            return False

    def search(
        self, query: Dict[str, Any], index_name: str = None, size: int = None
    ) -> Dict[str, Any]:
        """
        Execute a search query against specified index.

        Args:
            query: The Elasticsearch query body
            index_name: Name of the index to search (defaults to memory index)
            size: Maximum number of results to return (if not already in query body)

        Returns:
            Dict containing search results
        """
        try:
            index = index_name if index_name else self.memory_index_name

            # If size is provided and not in the query, add it
            if size is not None and "size" not in query:
                query["size"] = size

            response = self.es.search(index=index, body=query)
            # In Elasticsearch 8.x, response is directly the dict
            return response
        except Exception as e:
            raise Exception(f"Search operation failed: {str(e)}")

    def check_document_exists(self, index_name: str, doc_id: str) -> bool:
        """
        Check if a document exists in the specified index.

        Args:
            index_name: Name of the index to check
            doc_id: Document ID to check for

        Returns:
            bool: True if document exists, False otherwise
        """
        try:
            response = self.es.exists(index=index_name, id=doc_id)
            # In Elasticsearch 8.x, response is directly a boolean
            return response
        except Exception:
            return False

    def update_document(
        self, index_name: str, doc_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update specific fields in a document.

        Args:
            index_name: Name of the index containing the document
            doc_id: ID of the document to update
            updates: Dictionary of fields to update

        Returns:
            Dict containing the response or None if update failed
        """
        try:
            # Use options for ES 8.x compatibility
            client = self.es.options(ignore_status=[404])
            response = client.update(index=index_name, id=doc_id, body={"doc": updates})
            # In Elasticsearch 8.x, response is directly the dict
            return response
        except Exception as e:
            raise Exception(f"Document update failed: {str(e)}")
