import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from anthropic.types import RedactedThinkingBlock, TextBlock, ThinkingBlock, ToolUseBlock

from domain.models.enums import ContentType


@dataclass
class MessageContent:
    """
    Represents a single content item in a message.

    In Anthropic API, the content field of a message is a list of objects,
    each with a type and additional fields depending on the type.
    This class represents one item in that list.

    Attributes:
        type: Type of content (text, tool_use, etc.)
        text: Text content (for text type)
        tool_call: Tool call data (for tool_use type)
        tool_result: Tool result data (for tool_result type)
        image_url: Image URL data (for image type)
    """

    type: ContentType
    text: Optional[str] = None
    tool_call: Optional["ToolCall"] = None
    tool_result: Optional["ToolResponse"] = None
    image_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def make_text(cls, content: str) -> "MessageContent":
        """Create a text content item."""
        return cls(type=ContentType.TEXT, text=content)

    @classmethod
    def make_tool_call(cls, tool_call: "ToolCall") -> "MessageContent":
        """Create a tool call content item from a ToolCall object."""
        return cls(type=ContentType.TOOL_CALL, tool_call=tool_call)

    @classmethod
    def simple_tool_call(
        cls, name: str, input_data: Dict[str, Any], tool_id: Optional[str] = None
    ) -> "MessageContent":
        """Create a tool call content item directly from parameters."""
        if tool_id is None:
            tool_id = str(uuid.uuid4())

        tool_call = ToolCall(tool_name=name, tool_input=input_data, tool_id=tool_id)
        return cls(type=ContentType.TOOL_CALL, tool_call=tool_call)

    @classmethod
    def make_tool_result(cls, tool_response: "ToolResponse") -> "MessageContent":
        """Create a tool result content item from a ToolResponse object."""
        return cls(type=ContentType.TOOL_RESULT, tool_result=tool_response)

    @classmethod
    def simple_tool_result(
        cls, tool_id: str, output: Any, error: Optional[bool] = None
    ) -> "MessageContent":
        """Create a tool result content item directly from parameters."""
        tool_response = ToolResponse(tool_id=tool_id, content=output, is_error=error)
        return cls(type=ContentType.TOOL_RESULT, tool_result=tool_response)

    @classmethod
    def make_image(cls, url: str) -> "MessageContent":
        """Create an image content item."""
        return cls(type=ContentType.IMAGE, image_url=url)

    @classmethod
    def from_api_content(
        cls, content_item: TextBlock | ToolUseBlock | ThinkingBlock | RedactedThinkingBlock
    ) -> "MessageContent":
        """Create a MessageContent from an API content item."""
        content_type = content_item.get("type")

        if isinstance(content_item, TextBlock):
            return cls.make_text(content_item.text)

        elif isinstance(content_item, ToolUseBlock):
            # Create a ToolCall object from the API data
            tool_call = ToolCall(
                tool_name=content_item.name,
                tool_input=content_item.input.__dict__,
                tool_id=content_item.id,
            )
            return cls(
                type=ContentType.TOOL_CALL, tool_call=tool_call, raw_data=content_item.__dict__
            )

        else:
            # For unknown content types, store the raw data and return a generic instance
            return cls(
                type=ContentType.TEXT if content_type is None else ContentType(content_type),
                raw_data=content_item.__dict__,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for API."""
        if self.raw_data is not None:
            # If we have raw data from the API, use it for serialization
            return self.raw_data

        content_dict = {"type": self.type.value}

        if self.type == ContentType.TEXT and self.text is not None:
            content_dict["text"] = self.text

        elif self.type == ContentType.TOOL_CALL and self.tool_call is not None:
            # Format for Anthropic's tool_use block
            content_dict = {
                "type": "tool_use",
                "id": self.tool_call.tool_id,
                "name": self.tool_call.tool_name,
                "input": self.tool_call.tool_input,
            }

        elif self.type == ContentType.TOOL_RESULT and self.tool_result is not None:
            # Format for Anthropic's tool_result block
            content_dict = {"type": "tool_result", "tool_use_id": self.tool_result.tool_id}

            if self.tool_result.is_error is not None:
                content_dict["is_error"] = self.tool_result.is_error
            else:
                content_dict["content"] = self.tool_result.content

        elif self.type == ContentType.IMAGE and self.image_url is not None:
            # Format for Anthropic's image block
            content_dict = {"type": "image", "source": {"type": "url", "url": self.image_url}}

        return content_dict


@dataclass
class ToolCall:
    """
    Represents a tool call from an agent.

    Attributes:
        tool_name: Name of the tool to call
        tool_input: Parameters for the tool call
        tool_id: Unique identifier for the tool call
    """

    tool_name: str
    tool_input: Dict[str, Any]
    tool_id: str


@dataclass
class ToolResponse:
    """
    Response from a tool execution.

    Attributes:
        tool_id: ID of the tool call this is responding to
        content: Response content
        error: Optional error message if tool execution failed
    """

    tool_id: str
    content: str | List[MessageContent]
    is_error: Optional[bool] = False
    type: str = "tool_result"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        if self.is_error:
            return {
                "type": self.type,
                "tool_id": self.tool_id,
                "content": self.content,
                "is_error": self.is_error,
            }
        else:
            return {
                "type": self.type,
                "tool_id": self.tool_id,
                "content": self.content,
            }
