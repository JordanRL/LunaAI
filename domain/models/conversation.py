from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, TypeVar, Generic, cast
from datetime import datetime
import uuid
from enum import Enum
from anthropic.types import Message as AnthropicMessage, ToolUseBlock, TextBlock, ThinkingBlock, RedactedThinkingBlock

from domain.models.routing import ToolCall, ToolResponse


class ContentType(Enum):
    """Types of content in a message."""
    TEXT = "text"
    TOOL_CALL = "tool_use"  # Anthropic API uses "tool_use" for tool calls
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    # Add other content types as needed


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
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResponse] = None
    image_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def make_text(cls, content: str) -> 'MessageContent':
        """Create a text content item."""
        return cls(type=ContentType.TEXT, text=content)
    
    @classmethod
    def make_tool_call(cls, tool_call: ToolCall) -> 'MessageContent':
        """Create a tool call content item from a ToolCall object."""
        return cls(type=ContentType.TOOL_CALL, tool_call=tool_call)
    
    @classmethod
    def simple_tool_call(cls, name: str, input_data: Dict[str, Any], tool_id: Optional[str] = None) -> 'MessageContent':
        """Create a tool call content item directly from parameters."""
        if tool_id is None:
            tool_id = str(uuid.uuid4())
            
        tool_call = ToolCall(
            tool_name=name,
            tool_input=input_data,
            tool_id=tool_id
        )
        return cls(type=ContentType.TOOL_CALL, tool_call=tool_call)
    
    @classmethod
    def make_tool_result(cls, tool_response: ToolResponse) -> 'MessageContent':
        """Create a tool result content item from a ToolResponse object."""
        return cls(type=ContentType.TOOL_RESULT, tool_result=tool_response)
    
    @classmethod
    def simple_tool_result(cls, tool_id: str, output: Any, error: Optional[bool] = None) -> 'MessageContent':
        """Create a tool result content item directly from parameters."""
        tool_response = ToolResponse(
            tool_id=tool_id,
            content=output,
            is_error=error
        )
        return cls(type=ContentType.TOOL_RESULT, tool_result=tool_response)
    
    @classmethod
    def make_image(cls, url: str) -> 'MessageContent':
        """Create an image content item."""
        return cls(type=ContentType.IMAGE, image_url=url)
    
    @classmethod
    def from_api_content(cls, content_item: TextBlock|ToolUseBlock|ThinkingBlock|RedactedThinkingBlock) -> 'MessageContent':
        """Create a MessageContent from an API content item."""
        content_type = content_item.get("type")
        
        if isinstance(content_item, TextBlock):
            return cls.make_text(content_item.text)
            
        elif isinstance(content_item, ToolUseBlock):
            # Create a ToolCall object from the API data
            tool_call = ToolCall(
                tool_name=content_item.name,
                tool_input=content_item.input.__dict__,
                tool_id=content_item.id
            )
            return cls(type=ContentType.TOOL_CALL, tool_call=tool_call, raw_data=content_item.__dict__)
            
        else:
            # For unknown content types, store the raw data and return a generic instance
            return cls(type=ContentType.TEXT if content_type is None else ContentType(content_type), raw_data=content_item.__dict__)
    
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
                "input": self.tool_call.tool_input
            }
            
        elif self.type == ContentType.TOOL_RESULT and self.tool_result is not None:
            # Format for Anthropic's tool_result block
            content_dict = {
                "type": "tool_result",
                "tool_use_id": self.tool_result.tool_id
            }
            
            if self.tool_result.is_error is not None:
                content_dict["is_error"] = self.tool_result.is_error
            else:
                content_dict["content"] = self.tool_result.content
                
        elif self.type == ContentType.IMAGE and self.image_url is not None:
            # Format for Anthropic's image block
            content_dict = {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": self.image_url
                }
            }
            
        return content_dict


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
    def user(cls, text: str) -> 'Message':
        """Create a simple user text message."""
        return cls(
            role="user",
            content=[MessageContent.make_text(text)]
        )
    
    @classmethod
    def user_with_tool_result(cls, tool_id: str, result: Any, error: Optional[str] = None) -> 'Message':
        """Create a user message with tool result."""
        return cls(
            role="user",
            content=[MessageContent.simple_tool_result(tool_id, result, error)]
        )
    
    @classmethod
    def assistant(cls, text: str) -> 'Message':
        """Create a simple assistant text message."""
        return cls(
            role="assistant",
            content=[MessageContent.make_text(text)]
        )
    
    @classmethod
    def assistant_with_tool_call(cls, tool_name: str, tool_input: Dict[str, Any]) -> 'Message':
        """Create an assistant message with a tool call."""
        return cls(
            role="assistant",
            content=[MessageContent.simple_tool_call(tool_name, tool_input)]
        )
    
    @classmethod
    def system(cls, text: str) -> 'Message':
        """Create a simple system text message."""
        return cls(
            role="system",
            content=[MessageContent.make_text(text)]
        )
    
    @classmethod
    def from_anthropic_message(cls, message: AnthropicMessage) -> 'Message':
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
            message_id=message.get("id", str(uuid.uuid4())) if "id" in message else str(uuid.uuid4())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for API."""
        if self.has_tool_results():
            for result in self.get_tool_results():
                if result.is_error is not None:
                    return {
                        "role": "user",
                        "content": [],
                    }

        return {
            "role": self.role,
            "content": [item.to_dict() for item in self.content]
        }
    
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
        return " ".join(item.text or "" for item in self.content if item.type == ContentType.TEXT and item.text)
    
    def get_tool_calls(self) -> List[ToolCall]:
        """Get all tool calls."""
        return [item.tool_call for item in self.content 
                if item.type == ContentType.TOOL_CALL and item.tool_call is not None]
    
    def get_tool_results(self) -> List[ToolResponse]:
        """Get all tool results."""
        return [item.tool_result for item in self.content 
                if item.type == ContentType.TOOL_RESULT and item.tool_result is not None]
    
    def add_content(self, content_item: MessageContent) -> None:
        """Add a content item to this message."""
        self.content.append(content_item)


@dataclass
class ConversationSummary:
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
    timestamp: datetime = field(default_factory=datetime.now)
    original_text: Optional[str] = None


@dataclass
class Conversation:
    """
    Represents a conversation between Luna and a user.
    
    Attributes:
        conversation_id: Unique identifier for this conversation
        user_id: ID of the user in this conversation
        messages: List of messages in the conversation
        summaries: List of summaries of older parts of the conversation
        start_time: When the conversation started
        metadata: Additional data associated with this conversation
    """
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    messages: List[Message] = field(default_factory=list)
    summaries: List[ConversationSummary] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _summarized_ranges: List[Tuple[int, int]] = field(default_factory=list)

    def add_message(self, message: Message) -> 'Conversation':
        """Add a message to the conversation."""
        self.messages.append(message)
        return self
    
    def add_user_message(self, content: Union[str, MessageContent, List[MessageContent], Message]) -> 'Conversation':
        """Add a user message to the conversation."""
        if isinstance(content, str):
            message = Message.user(content)
        elif isinstance(content, MessageContent):
            message = Message(role="user", content=[content])
        elif isinstance(content, list) and all(isinstance(item, MessageContent) for item in content):
            message = Message(role="user", content=content)
        elif isinstance(content, Message):
            if content.role != "user":
                raise ValueError(f"Expected user message, got {content.role}")
            message = content
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
            
        self.messages.append(message)
        return self

    def add_assistant_message(self, content: Union[str, MessageContent, List[MessageContent], Message]) -> 'Conversation':
        """Add an assistant message to the conversation."""
        if isinstance(content, str):
            message = Message.assistant(content)
        elif isinstance(content, MessageContent):
            message = Message(role="assistant", content=[content])
        elif isinstance(content, list) and all(isinstance(item, MessageContent) for item in content):
            message = Message(role="assistant", content=content)
        elif isinstance(content, Message):
            if content.role != "assistant":
                raise ValueError(f"Expected assistant message, got {content.role}")
            message = content
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
            
        self.messages.append(message)
        return self
    
    def add_system_message(self, content: str) -> 'Conversation':
        """Add a system message to the conversation."""
        message = Message.system(content)
        self.messages.append(message)
        return self
    
    def add_user_tool_result(self, tool_id: str, result: Any, error: Optional[str] = None) -> 'Conversation':
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