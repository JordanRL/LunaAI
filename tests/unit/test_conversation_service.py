"""
Unit tests for the ConversationService.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from domain.models.content import MessageContent
from domain.models.conversation import Conversation
from domain.models.messages import Message
from domain.models.user import UserProfile, UserRelationship
from services.conversation_service import ConversationService
from services.user_service import UserService


class TestConversationService(unittest.TestCase):
    """Tests for the ConversationService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock UserService
        self.mock_user_service = MagicMock(spec=UserService)

        # Configure the mock UserService to return expected values
        self.mock_user_service.create_or_get_user.return_value = (
            False,
            UserProfile(user_id="test_user"),
            {"user_id": "test_user"},
        )

        # Create conversation service with mock user service
        self.conversation_service = ConversationService(self.mock_user_service)

        # Create a test conversation
        self.test_conversation = Conversation(
            conversation_id="test_conversation", user_id="test_user"
        )
        self.conversation_service.conversations["test_conversation"] = self.test_conversation

    def test_get_conversation(self):
        """Test retrieving a conversation by ID."""
        # Test retrieving existing conversation
        conversation = self.conversation_service.get_conversation("test_conversation")
        self.assertEqual(conversation, self.test_conversation)

        # Test retrieving non-existent conversation
        conversation = self.conversation_service.get_conversation("non_existent")
        self.assertIsNone(conversation)

    def test_create_conversation(self):
        """Test creating a new conversation."""
        # Test creating a conversation for an existing user
        conversation = self.conversation_service.create_conversation("test_user")

        # Verify the conversation was created with the correct user_id
        self.assertEqual(conversation.user_id, "test_user")
        self.assertIsNotNone(conversation.conversation_id)

        # Verify the conversation was added to the service
        self.assertIn(conversation.conversation_id, self.conversation_service.conversations)

        # Verify user service methods were called
        self.mock_user_service.create_or_get_user.assert_called_with("test_user")
        self.mock_user_service.update_interaction_stats.assert_called_with("test_user")

        # Test creating a conversation for a new user
        self.mock_user_service.create_or_get_user.return_value = (
            True,
            UserProfile(user_id="new_user"),
            {"user_id": "new_user"},
        )

        conversation = self.conversation_service.create_conversation("new_user")

        # Verify the conversation was created with the correct user_id
        self.assertEqual(conversation.user_id, "new_user")

        # Verify user service methods were called
        self.mock_user_service.create_or_get_user.assert_called_with("new_user")
        # Update interaction stats should not be called for new users
        self.mock_user_service.update_interaction_stats.assert_called_once_with("test_user")

    def test_get_conversation_id_by_user_id(self):
        """Test retrieving a conversation ID by user ID."""
        # Add a test conversation for the user
        test_conversation = Conversation(conversation_id="user_conversation", user_id="test_user")
        self.conversation_service.conversations["user_conversation"] = test_conversation

        # Test retrieving conversation ID
        conversation_id = self.conversation_service.get_conversation_id_by_user_id("test_user")
        self.assertEqual(conversation_id, "user_conversation")

        # Test retrieving conversation ID for user with no conversations
        conversation_id = self.conversation_service.get_conversation_id_by_user_id("non_existent")
        self.assertIsNone(conversation_id)

    def test_add_user_message(self):
        """Test adding a user message to a conversation."""
        # Create test message content
        content = MessageContent.make_text("Hello, Luna!")

        # Add message to conversation
        conversation = self.conversation_service.add_user_message("test_conversation", content)

        # Verify the message was added
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, "user")
        self.assertEqual(conversation.messages[0].content[0].text, "Hello, Luna!")

        # Verify user service methods were called
        self.mock_user_service.update_interaction_stats.assert_called_with("test_user")

        # Test adding to non-existent conversation
        with self.assertRaises(ValueError):
            self.conversation_service.add_user_message("non_existent", content)

    def test_add_assistant_message(self):
        """Test adding an assistant message to a conversation."""
        # Create test message content
        content = MessageContent.make_text("I'm Luna, how can I help?")

        # Add message to conversation
        conversation = self.conversation_service.add_assistant_message("test_conversation", content)

        # Verify the message was added
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, "assistant")
        self.assertEqual(conversation.messages[0].content[0].text, "I'm Luna, how can I help?")

        # Test adding to non-existent conversation
        with self.assertRaises(ValueError):
            self.conversation_service.add_assistant_message("non_existent", content)

    def test_add_message(self):
        """Test adding a message to a conversation."""
        # Create test messages
        user_message = Message.user("Hello from user")
        assistant_message = Message.assistant("Hello from assistant")
        system_message = Message.system("System configuration")

        # Add messages to conversation
        self.conversation_service.add_message("test_conversation", user_message)
        self.conversation_service.add_message("test_conversation", assistant_message)
        self.conversation_service.add_message("test_conversation", system_message)

        # Verify the messages were added
        conversation = self.conversation_service.get_conversation("test_conversation")
        self.assertEqual(len(conversation.messages), 3)
        self.assertEqual(conversation.messages[0].role, "user")
        self.assertEqual(conversation.messages[1].role, "assistant")
        self.assertEqual(conversation.messages[2].role, "system")

        # Verify user service methods were called for user message but not for other types
        self.mock_user_service.update_interaction_stats.assert_called_once_with("test_user")

        # Test adding to non-existent conversation
        with self.assertRaises(ValueError):
            self.conversation_service.add_message("non_existent", user_message)

    def test_get_recent_history(self):
        """Test retrieving recent messages from a conversation."""
        # Add multiple messages to conversation
        conversation = self.conversation_service.get_conversation("test_conversation")
        for i in range(15):
            message = Message.user(f"Message {i}")
            conversation.add_message(message)

        # Test retrieving recent messages with default limit
        recent_messages = self.conversation_service.get_recent_history("test_conversation")
        self.assertEqual(len(recent_messages), 10)
        self.assertEqual(recent_messages[0].get_text(), "Message 5")
        self.assertEqual(recent_messages[9].get_text(), "Message 14")

        # Test retrieving with custom limit
        recent_messages = self.conversation_service.get_recent_history("test_conversation", limit=5)
        self.assertEqual(len(recent_messages), 5)
        self.assertEqual(recent_messages[0].get_text(), "Message 10")

        # Test retrieving from non-existent conversation
        recent_messages = self.conversation_service.get_recent_history("non_existent")
        self.assertEqual(len(recent_messages), 0)

    def test_summarize_conversation(self):
        """Test generating a summary of a conversation."""
        # Add messages to conversation
        conversation = self.conversation_service.get_conversation("test_conversation")
        conversation.add_user_message("Hello")
        conversation.add_assistant_message("Hi there")
        conversation.add_user_message("How are you?")
        conversation.add_assistant_message("I'm doing well")

        # Test summarizing conversation
        summary = self.conversation_service.summarize_conversation("test_conversation")
        self.assertIsNotNone(summary)
        self.assertIn("test_user", summary)
        self.assertIn("4 messages", summary)
        self.assertIn("2 from user", summary)
        self.assertIn("2 from assistant", summary)

        # Test summarizing non-existent conversation
        summary = self.conversation_service.summarize_conversation("non_existent")
        self.assertIsNone(summary)

    def test_get_conversation_by_user(self):
        """Test retrieving all conversations for a user."""
        # Add multiple conversations for the user
        conversation1 = Conversation(conversation_id="user_conversation1", user_id="test_user")
        conversation2 = Conversation(conversation_id="user_conversation2", user_id="test_user")
        conversation3 = Conversation(conversation_id="other_conversation", user_id="other_user")

        self.conversation_service.conversations["user_conversation1"] = conversation1
        self.conversation_service.conversations["user_conversation2"] = conversation2
        self.conversation_service.conversations["other_conversation"] = conversation3

        # Test retrieving conversations for user
        user_conversations = self.conversation_service.get_conversation_by_user("test_user")
        self.assertEqual(len(user_conversations), 3)  # includes test_conversation from setUp

        # Test retrieving conversations for user with no conversations
        user_conversations = self.conversation_service.get_conversation_by_user("non_existent")
        self.assertEqual(len(user_conversations), 0)

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        # Test deleting existing conversation
        result = self.conversation_service.delete_conversation("test_conversation")
        self.assertTrue(result)
        self.assertNotIn("test_conversation", self.conversation_service.conversations)

        # Test deleting non-existent conversation
        result = self.conversation_service.delete_conversation("non_existent")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
