from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from domain.models.pydantic_ai.content import ToolCall
from domain.models.pydantic_ai.enums import AgentType


class RoutingInstruction(BaseModel):
    """
    Routing instruction for agent-to-agent communication.

    This model defines how messages should be routed between agents,
    including the source and target agents and the message content.

    Attributes:
        source_agent: The agent sending the request
        tool_call: The tool call that triggered the routing
        message_override: Optional override for the message being routed
    """

    source_agent: AgentType
    tool_call: ToolCall
    message_override: Optional[str] = None

    def is_agent_routing(self) -> bool:
        """
        Check if this routing instruction is for agent-to-agent communication.

        Returns:
            True if the routing is intended for another agent, False otherwise
        """
        # Check if the tool name matches the pattern for agent routing
        return self.tool_call.tool_name == "route_to_agent"

    def get_target_agent(self) -> Optional[str]:
        """
        Get the target agent for this routing instruction.

        Returns:
            The name of the target agent, or None if not an agent routing
        """
        if not self.is_agent_routing():
            return None

        input_data = self.tool_call.tool_input
        return input_data.get("target_agent", None) if isinstance(input_data, dict) else None

    def get_message(self) -> str:
        """
        Get the message for this routing instruction.

        Returns:
            The message to route, or a default message if none is provided
        """
        if self.message_override:
            return self.message_override

        if not self.is_agent_routing():
            return f"Tool call: {self.tool_call.tool_name}"

        input_data = self.tool_call.tool_input
        message = (
            input_data.get("message", "No message content provided")
            if isinstance(input_data, dict)
            else "No message content provided"
        )
        return message


class StateRouting(BaseModel):
    """
    Configuration for agent routing in the system.

    This model defines how messages should flow between agents
    in the multi-agent system, including pre-routing, routing,
    and post-routing agents.
    """

    # Agent lists
    pre_routing_agents: list[AgentType] = Field(default_factory=list)
    routing_agents: list[AgentType] = Field(default_factory=list)
    post_routing_agents: list[AgentType] = Field(default_factory=list)
    output_agent: AgentType = AgentType.OUTPUTTER

    class Config:
        arbitrary_types_allowed = True
