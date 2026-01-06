from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from domain.models.pydantic_ai.content import MessageContent
from domain.models.pydantic_ai.messages import Message


class ConversationSummary(BaseModel):
    """
    Summary of a portion of a conversation.

    Attributes:
        content: Summary text
        range: Range of messages that were summarized (indices)
        message_ids: IDs of messages that were summarized
        timestamp: When the summary was created
        original_text: Original text that was summarized
    """

    content: str
    range: Tuple[int, int]  # start_idx, end_idx
    message_ids: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    original_text: Optional[str] = None


class Conversation(BaseModel):
    """
    Represents a conversation between Luna and a user.

    This model is used to track message history and provides
    utility methods for adding messages and generating summaries.

    Attributes:
        conversation_id: Unique identifier for this conversation
        user_id: ID of the user in this conversation
        messages: List of messages in the conversation
        summaries: List of summaries of older parts of the conversation
        start_time: When the conversation started
        metadata: Additional data associated with this conversation
    """

    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = "default_user"
    messages: List[Message] = Field(default_factory=list)
    summaries: List[ConversationSummary] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    _summarized_ranges: List[Tuple[int, int]] = Field(default_factory=list, exclude=True)

    def add_message(self, message: Message) -> "Conversation":
        """Add a message to the conversation."""
        if message.role not in ["user", "assistant", "system"]:
            raise ValueError(f"Invalid role: {message.role}")

        self.messages.append(message)
        return self

    def add_user_message(
        self, content: Union[str, MessageContent, List[MessageContent], Message]
    ) -> "Conversation":
        """Add a user message to the conversation."""
        if isinstance(content, str):
            message = Message.user(content)
        elif isinstance(content, dict) and "type" in content:
            # Assume it's a content dict
            message = Message(role="user", content=[content])
        elif isinstance(content, BaseModel) and hasattr(content, "type"):
            # Assume it's a MessageContent
            message = Message(role="user", content=[content])
        elif isinstance(content, list):
            # Assume list of MessageContent
            message = Message(role="user", content=content)
        elif isinstance(content, Message):
            if content.role != "user":
                raise ValueError(f"Expected user message, got {content.role}")
            message = content
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

        self.messages.append(message)
        return self

    def add_assistant_message(
        self, content: Union[str, MessageContent, List[MessageContent], Message]
    ) -> "Conversation":
        """Add an assistant message to the conversation."""
        if isinstance(content, str):
            message = Message.assistant(content)
        elif isinstance(content, dict) and "type" in content:
            # Assume it's a content dict
            message = Message(role="assistant", content=[content])
        elif isinstance(content, BaseModel) and hasattr(content, "type"):
            # Assume it's a MessageContent
            message = Message(role="assistant", content=[content])
        elif isinstance(content, list):
            # Assume list of MessageContent
            message = Message(role="assistant", content=content)
        elif isinstance(content, Message):
            if content.role != "assistant":
                raise ValueError(f"Expected assistant message, got {content.role}")
            message = content
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

        self.messages.append(message)
        return self

    def add_system_message(self, content: str) -> "Conversation":
        """Add a system message to the conversation."""
        message = Message.system(content)
        self.messages.append(message)
        return self

    def add_user_tool_result(
        self, tool_id: str, result: Any, error: bool = False
    ) -> "Conversation":
        """Add a user message with a tool result."""
        message = Message.user_with_tool_result(tool_id, result, error)
        self.messages.append(message)
        return self

    def get_last_n_messages(self, n: int = 10) -> List[Message]:
        """Get the last n messages."""
        return self.messages[-n:] if len(self.messages) >= n else self.messages.copy()

    def to_api_messages(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert conversation to format for API calls."""
        messages_to_include = self.messages
        if n is not None:
            messages_to_include = self.get_last_n_messages(n)

        return [msg.to_dict() for msg in messages_to_include]

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to this message."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Any:
        """Get metadata from this message."""
        return self.metadata.get(key, None)

    # Integration with PydanticAI's MessageHistory
    def to_message_history(self) -> List[Dict[str, Any]]:
        """Convert to PydanticAI's message history format."""
        return [msg.to_dict() for msg in self.messages]
