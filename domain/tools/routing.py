"""
Routing tools for agent-to-agent communication.
"""

from typing import Dict, List, Any, Optional
from domain.models.tool import Tool, ToolCategory
from domain.models.enums import AgentType
from debug import debug_manager, DebugLevel, log, log_error


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
                        "enum": AgentType.filtered_to_list()
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send to the target agent"
                    },
                    "await_response": {
                        "type": "boolean",
                        "description": "Whether to await a response from the target agent",
                        "default": False
                    }
                },
                "required": ["target_agent", "message"]
            },
            handler=self.handle,
            category=ToolCategory.ROUTING
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process an agent routing request."""
        target_agent = tool_input.get("target_agent")
        message = tool_input.get("message")
        await_response = tool_input.get("await_response", False)
        
        log(f"Routing request: {target_agent} | Await response: {await_response}", 
           DebugLevel.MINIMAL, debug_manager.symbols.ROUTING)
        
        # Show message preview in VERBOSE mode
        if debug_manager.should_debug(DebugLevel.VERBOSE):
            message_preview = debug_manager.truncate_content(message, 150)
            log(f"  Message: {message_preview}", DebugLevel.VERBOSE)
        
        # Validate target agent
        if target_agent not in AgentType.filtered_to_list():
            error_msg = f"Invalid target agent: {target_agent}"
            log_error(error_msg, "routing_validation")
            
            # Show available agents in VERBOSE mode
            if debug_manager.should_debug(DebugLevel.VERBOSE):
                valid_agents = ", ".join(AgentType.filtered_to_list())
                log(f"  Valid agents: {valid_agents}", DebugLevel.VERBOSE)
                
            return {
                "routing_success": False,
                "error": error_msg,
                "valid_agents": AgentType.filtered_to_list()
            }
        
        return {
            "target_agent": target_agent,
            "message": message,
            "await_response": await_response,
            "routing_success": True
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
                    }
                },
                "required": ["current_thoughts", "reason"]
            },
            handler=self.handle,
            category=ToolCategory.ROUTING
        )
    
    def handle(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a continue thinking request."""
        reason = tool_input.get("reason")
        current_thoughts = tool_input.get("current_thoughts")

        return {
            "reason": reason,
            "current_thoughts": current_thoughts
        }