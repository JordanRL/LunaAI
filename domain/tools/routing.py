"""
Routing tools for agent-to-agent communication.
"""

from typing import Any, Dict, List, Optional

from domain.models.enums import AgentType
from domain.models.tool import Tool, ToolCategory


class RouteToAgentTool(Tool):
    """Tool for routing messages between agents."""

    def __init__(self):
        """Initialize the route to agent tool."""
        super().__init__(
            name="route_to_agent",
            description="""Route a message to another agent with optional response handling.

Your message content for the target agent should have plenty of specific details.

To use this tool, specify which agent you want to communicate with and provide a clear message.
Set await_response to true if you need information back from the agent.""",
            input_schema={
                "type": "object",
                "properties": {
                    "target_agent": {
                        "type": "string",
                        "description": "The agent to route this message to",
                        "enum": AgentType.filtered_to_list(),
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send to the target agent",
                    },
                    "await_response": {
                        "type": "boolean",
                        "description": "Whether to await a response from the target agent",
                        "default": False,
                    },
                },
                "required": ["target_agent", "message"],
            },
            handler=self.handle,
            category=ToolCategory.ROUTING,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process an agent routing request."""
        target_agent = tool_input.get("target_agent")
        message = tool_input.get("message")
        await_response = tool_input.get("await_response", False)

        # Validate target agent
        if target_agent not in AgentType.filtered_to_list():
            error_msg = f"Invalid target agent: {target_agent}"
            return {
                "routing_success": False,
                "error": error_msg,
                "valid_agents": AgentType.filtered_to_list(),
            }

        return {
            "target_agent": target_agent,
            "message": message,
            "await_response": await_response,
            "routing_success": True,
        }


class ContinueThinkingTool(Tool):
    """Tool for allowing agents to continue thinking."""

    def __init__(self):
        """Initialize the continue thinking tool."""
        super().__init__(
            name="continue_thinking",
            description="""Receive a response from the system that gives you an additional round of thinking.

Use this tool when you feel like you need additional time to think. You receive a user message back
which contains your thoughts and the reason you wanted more time to think.

You may only use this tool once per turn.""",
            input_schema={
                "type": "object",
                "properties": {
                    "current_thoughts": {
                        "type": "string",
                        "description": "Your current thoughts that you want to receive back to allow more thinking time",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason to continue thinking",
                    },
                },
                "required": ["current_thoughts", "reason"],
            },
            handler=self.handle,
            category=ToolCategory.ROUTING,
        )

    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a continue thinking request."""
        reason = tool_input.get("reason")
        current_thoughts = tool_input.get("current_thoughts")

        return {"reason": reason, "current_thoughts": current_thoughts}
