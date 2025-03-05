from dataclasses import dataclass
from typing import Optional

from domain.models.enums import AgentType
from domain.models.content import ToolCall


@dataclass
class RoutingInstruction:
    """
    Defines how a message should be routed between agents or tools.
    
    Attributes:
        source_agent: The agent that created this routing instruction
        tool_call: Tool call to execute if this is a tool routing instruction
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