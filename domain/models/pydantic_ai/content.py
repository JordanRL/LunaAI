from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_ai.messages import (
    ModelRequest,
    ModelRequestPart,
    ModelResponse,
    ModelResponsePart,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from domain.models.pydantic_ai.enums import ContentType


class ToolCall:
    """
    Represents a tool call from an agent.

    This is a provider-agnostic representation of a tool call,
    which can be converted to/from provider-specific formats.
    """

    tool_name: str
    tool_input: Dict[str, Any]
    tool_id: str = Field(default_factory=lambda: str(uuid4()))


class ToolReturn:
    """
    Response from a tool execution.

    This is a provider-agnostic representation of a tool response,
    which can be converted to/from provider-specific formats.
    """

    tool_id: str
    content: Union[str, List[Any], Dict[str, Any]]
    is_error: bool = False
    type: Literal["tool_result"] = "tool_result"


class TextContent:
    """Text content in a message."""

    type: Literal[ContentType.TEXT] = ContentType.TEXT
    text: str


class ToolCallContent(ToolCallPart):
    """Tool call content in a message."""

    type: Literal[ContentType.TOOL_CALL] = ContentType.TOOL_CALL
    tool_call: ToolCall


class ToolReturnContent(ToolReturnPart):
    """Tool result content in a message."""

    type: Literal[ContentType.TOOL_RESULT] = ContentType.TOOL_RESULT
    tool_result: ToolReturn


class ThinkingContent:
    """Thinking content in a message, for models that support thinking mode."""

    type: Literal[ContentType.THINKING] = ContentType.THINKING
    thinking: str
