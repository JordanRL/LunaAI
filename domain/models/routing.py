from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum

from domain.models.enums import AgentType
from domain.models.messages import MessageContent


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
    content: str|List[MessageContent]
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

@dataclass
class RoutingInstruction:
    """
    Defines how a message should be routed between agents or tools.
    
    Attributes:
        source_agent: The agent that created this routing instruction
        tool_call: Tool call to execute if this is a tool routing instruction
        content: Optional text content associated with this routing
        metadata: Additional data associated with this routing
    """
    source_agent: AgentType
    tool_call: Optional[ToolCall] = None

    def __init__(
            self,
            source_agent: AgentType,
            tool_call: Optional[ToolCall] = None,
    ):
        self.source_agent = source_agent
        self.tool_call = tool_call

    def is_agent_routing(self) -> bool:
        """Check if this is routing to another agent."""
        return self.tool_call.tool_name == "route_to_agent"
    
    def is_tool_routing(self) -> bool:
        """Check if this is routing to a tool."""
        return self.tool_call is not None