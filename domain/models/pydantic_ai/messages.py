from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from pydantic_ai.messages import ModelMessage


class Message(ModelMessage):
    """
    Represents a message in a conversation.

    This model provides a provider-agnostic representation of a message,
    which can be converted to/from provider-specific formats.

    Attributes:
        role: Role of the sender (user, assistant, system)
        content: List of content items
        timestamp: When the message was sent
        message_id: Unique identifier for the message
        metadata: Additional data associated with this message
    """

    role: Literal["user", "assistant", "system"]
    content: List[MessageContent]
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Factory methods for creating common message types
    @classmethod
    def user(cls, text: str) -> "Message":
        """Create a simple user text message."""
        return cls(role="user", content=[make_text(text)])

    @classmethod
    def user_with_tool_result(cls, tool_id: str, result: Any, error: bool = False) -> "Message":
        """Create a user message with tool result."""
        tool_result = ToolResponse(tool_id=tool_id, content=result, is_error=error)
        return cls(role="user", content=[ToolResultContent(tool_result=tool_result)])

    @classmethod
    def assistant(cls, text: str) -> "Message":
        """Create a simple assistant text message."""
        return cls(role="assistant", content=[make_text(text)])

    @classmethod
    def assistant_with_tool_call(cls, tool_name: str, tool_input: Dict[str, Any]) -> "Message":
        """Create an assistant message with a tool call."""
        return cls(role="assistant", content=[simple_tool_call(tool_name, tool_input)])

    @classmethod
    def system(cls, text: str) -> "Message":
        """Create a simple system text message."""
        return cls(role="system", content=[make_text(text)])

    # Utility methods for accessing message content
    def has_text(self) -> bool:
        """Check if this message contains any text content."""
        return any(isinstance(item, TextContent) for item in self.content)

    def has_tool_calls(self) -> bool:
        """Check if this message contains any tool calls."""
        return any(isinstance(item, ToolCallContent) for item in self.content)

    def has_tool_results(self) -> bool:
        """Check if this message contains any tool results."""
        return any(isinstance(item, ToolResultContent) for item in self.content)

    def get_text(self) -> str:
        """Get all text content concatenated."""
        return " ".join(
            item.text for item in self.content if isinstance(item, TextContent) and item.text
        )

    def get_tool_calls(self) -> List[ToolCall]:
        """Get all tool calls."""
        return [
            item.tool_call
            for item in self.content
            if isinstance(item, ToolCallContent) and item.tool_call is not None
        ]

    def get_tool_results(self) -> List[ToolResponse]:
        """Get all tool results."""
        return [
            item.tool_result
            for item in self.content
            if isinstance(item, ToolResultContent) and item.tool_result is not None
        ]

    def add_content(self, content_item: MessageContent) -> None:
        """Add a content item to this message."""
        self.content.append(content_item)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to this message."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Any:
        """Get metadata from this message."""
        return self.metadata.get(key, None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for API."""
        # Always return all content, including tool responses with errors
        # This ensures that the API can match tool_use_id with tool_result blocks
        return {
            "role": self.role,
            "content": [self._content_to_dict(item) for item in self.content],
        }

    def _content_to_dict(self, content: Any) -> Dict[str, Any]:
        """Convert a content item to a dictionary for API use."""
        if isinstance(content, dict):
            return content
        elif hasattr(content, "model_dump"):
            return content.model_dump(exclude_none=True)
        elif hasattr(content, "to_dict"):
            return content.to_dict()
        else:
            # Fallback to string representation
            return {"type": "text", "text": str(content)}
