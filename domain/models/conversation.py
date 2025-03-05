from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import uuid

from domain.models.messages import MessageContent, Message


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

    def add_assistant_message(self, content: Union[str, MessageContent, List[
        MessageContent], Message]) -> 'Conversation':
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