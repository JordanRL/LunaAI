"""
Conversation service interface for Luna.

This module defines the interface for conversation management.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from domain.models.content import MessageContent
from domain.models.conversation import Conversation
from domain.models.messages import Message
from domain.models.routing import RoutingInstruction
from services.user_service import UserService


class ConversationService:
    """
    An in-memory implementation of the conversation service.

    This service manages conversations in memory without persistent storage.
    For a production system, this would be replaced with a database-backed
    implementation.
    """

    def __init__(self, user_service: UserService):
        """
        Initialize the conversation service.

        Args:
            user_service: Service for managing users
        """
        self.conversations: Dict[str, Conversation] = {}
        self.user_service = user_service

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation: The conversation or None if not found
        """
        return self.conversations.get(conversation_id)

    def get_conversation_id_by_user_id(self, user_id: str) -> Optional[str]:
        conversations = self.get_conversation_by_user(user_id)
        if len(conversations) > 0:
            conversation_id = conversations[-1].conversation_id
            return conversation_id
        return None

    def create_conversation(self, user_id: str) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User identifier

        Returns:
            Conversation: The new conversation
        """
        # Ensure the user exists
        is_new_user, user_profile, _ = self.user_service.create_or_get_user(user_id)

        # Update user interaction stats if this is an existing user
        if not is_new_user:
            self.user_service.update_interaction_stats(user_id)

        # Create a new conversation
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id, user_id=user_id, start_time=datetime.now()
        )

        # Store the conversation
        self.conversations[conversation_id] = conversation

        return conversation

    def create_internal_conversation(self):
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            conversation_id=conversation_id, user_id="internal", start_time=datetime.now()
        )

        self.conversations["internal"] = conversation
        return conversation

    def add_internal_thinking_message(self, content: MessageContent, agent: str):
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")

        conversation.add_message(Message(role=agent, content=[content]))
        return self

    def add_internal_tool_call_message(self, routing: RoutingInstruction, agent: str):
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")
        conversation.add_message(
            Message(
                role=agent + "_calling_tool_" + routing.tool_call.tool_name,
                content=[MessageContent.make_text(json.dumps(routing.tool_call.tool_input))],
            )
        )
        return self

    def add_internal_tool_response_message(
        self, content: MessageContent, agent: str, tool_name: str
    ):
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")
        conversation.add_message(
            Message(role=tool_name + "_responding_to_" + agent, content=[content])
        )
        return self

    def add_internal_routing_message(self, routing: RoutingInstruction):
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")
        conversation.add_message(
            Message(
                role=routing.source_agent.value
                + "_routing_to_agent_"
                + routing.tool_call.tool_input.get("target_agent"),
                content=[MessageContent.make_text(routing.tool_call.tool_input.get("message"))],
            )
        )
        return self

    def add_internal_routing_response_message(self, routing: RoutingInstruction, response: str):
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")
        conversation.add_message(
            Message(
                role=routing.tool_call.tool_input.get("target_agent")
                + "_responding_to_agent"
                + routing.source_agent.value,
                content=[MessageContent.make_text(response)],
            )
        )
        return self

    def compile_internal(self):
        result = ""
        conversation = self.get_conversation("internal")
        if not conversation:
            raise ValueError("Conversation internal not found")

        for message in conversation.messages:
            result += f"{message.role}: {message.content[0].text}\n\n"

        return result

    def add_user_message(self, conversation_id: str, content: MessageContent) -> Conversation:
        """
        Add a user message to a conversation.

        Args:
            conversation_id: Conversation identifier
            content: Message content

        Returns:
            Conversation: The updated conversation
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update user interaction stats
        self.user_service.update_interaction_stats(conversation.user_id)

        # Add the message
        conversation.add_user_message(content)

        return conversation

    def add_assistant_message(self, conversation_id: str, content: MessageContent) -> Conversation:
        """
        Add an assistant message to a conversation.

        Args:
            conversation_id: Conversation identifier
            content: Message content

        Returns:
            Conversation: The updated conversation
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Add the message
        conversation.add_assistant_message(content)

        return conversation

    def add_message(self, conversation_id: str, message: Message) -> Conversation:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation identifier
            message: Message to add

        Returns:
            Conversation: The updated conversation
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update user interaction stats if this is a user message
        if message.role == "user":
            self.user_service.update_interaction_stats(conversation.user_id)

        # Add the message
        conversation.add_message(message)

        return conversation

    def get_recent_history(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """
        Get recent messages from a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return

        Returns:
            List[Message]: Recent messages
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        return conversation.get_last_n_messages(limit)

    def summarize_conversation(self, conversation_id: str) -> Optional[str]:
        """
        Generate a summary of the conversation.

        This is an additional helper method not in the interface.

        Args:
            conversation_id: Conversation identifier

        Returns:
            str: Summary text or None if conversation not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        # In a real implementation, this would use an LLM to generate a summary
        # For now, just create a simple summary based on message count
        user_message_count = sum(1 for msg in conversation.messages if msg.role == "user")
        assistant_message_count = sum(1 for msg in conversation.messages if msg.role == "assistant")

        summary = (
            f"Conversation with user {conversation.user_id} started at {conversation.start_time}. "
            f"Contains {len(conversation.messages)} messages total: "
            f"{user_message_count} from user and {assistant_message_count} from assistant."
        )

        return summary

    def get_conversation_by_user(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user.

        This is an additional helper method not in the interface.

        Args:
            user_id: User identifier

        Returns:
            List[Conversation]: List of conversations
        """
        return [
            conversation
            for conversation in self.conversations.values()
            if conversation.user_id == user_id
        ]

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        This is an additional helper method not in the interface.

        Args:
            conversation_id: Conversation identifier

        Returns:
            bool: Whether the deletion was successful
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
