import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic.types import Message as AnthropicMessage

from domain.models.content import MessageContent, ToolCall, ToolResponse
from domain.models.enums import ContentType


@dataclass
class Message:
    """
    Represents a message in a conversation.

    In Anthropic API, a message has a role and a content field which is a list
    of content items. This class represents a complete message.

    Attributes:
        role: Role of the sender (user, assistant, system)
        content: List of content items
        timestamp: When the message was sent
        message_id: Unique identifier for the message
        metadata: Additional data associated with this message
    """

    role: str  # user, assistant, system
    content: List[MessageContent]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def user(cls, text: str) -> "Message":
        """Create a simple user text message."""
        return cls(role="user", content=[MessageContent.make_text(text)])

    @classmethod
    def user_with_tool_result(
        cls, tool_id: str, result: Any, error: Optional[str] = None
    ) -> "Message":
        """Create a user message with tool result."""
        return cls(role="user", content=[MessageContent.simple_tool_result(tool_id, result, error)])

    @classmethod
    def assistant(cls, text: str) -> "Message":
        """Create a simple assistant text message."""
        return cls(role="assistant", content=[MessageContent.make_text(text)])

    @classmethod
    def assistant_with_tool_call(cls, tool_name: str, tool_input: Dict[str, Any]) -> "Message":
        """Create an assistant message with a tool call."""
        return cls(
            role="assistant", content=[MessageContent.simple_tool_call(tool_name, tool_input)]
        )

    @classmethod
    def system(cls, text: str) -> "Message":
        """Create a simple system text message."""
        return cls(role="system", content=[MessageContent.make_text(text)])

    @classmethod
    def from_anthropic_message(cls, message: AnthropicMessage) -> "Message":
        """Create a Message from an Anthropic API message."""
        role = message.role
        content_items = message.content

        if isinstance(content_items, str):
            # Handle plain text content (legacy format)
            content = [MessageContent.make_text(content_items)]
        elif isinstance(content_items, list):
            # Handle list of content items
            content = [MessageContent.from_api_content(item) for item in content_items]
        else:
            raise ValueError(f"Unknown content format: {type(content_items)}")

        return cls(
            role=role,
            content=content,
            message_id=(
                message.get("id", str(uuid.uuid4())) if "id" in message else str(uuid.uuid4())
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for API."""
        # Always return all content, including tool responses with errors
        # This ensures that the API can match tool_use_id with tool_result blocks
        return {"role": self.role, "content": [item.to_dict() for item in self.content]}

    def has_text(self) -> bool:
        """Check if this message contains any text content."""
        return any(item.type == ContentType.TEXT for item in self.content)

    def has_tool_calls(self) -> bool:
        """Check if this message contains any tool calls."""
        return any(item.type == ContentType.TOOL_CALL for item in self.content)

    def has_tool_results(self) -> bool:
        """Check if this message contains any tool results."""
        return any(item.type == ContentType.TOOL_RESULT for item in self.content)

    def get_text(self) -> str:
        """Get all text content concatenated."""
        return " ".join(
            item.text or "" for item in self.content if item.type == ContentType.TEXT and item.text
        )

    def get_tool_calls(self) -> List[ToolCall]:
        """Get all tool calls."""
        return [
            item.tool_call
            for item in self.content
            if item.type == ContentType.TOOL_CALL and item.tool_call is not None
        ]

    def get_tool_results(self) -> List[ToolResponse]:
        """Get all tool results."""
        return [
            item.tool_result
            for item in self.content
            if item.type == ContentType.TOOL_RESULT and item.tool_result is not None
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
