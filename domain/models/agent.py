from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from domain.models.messages import Message
from domain.models.enums import AgentType
from domain.models.content import ToolCall
from domain.models.routing import RoutingInstruction
from domain.models.tool import Tool


@dataclass
class AgentResponse:
    """
    Response from an agent execution.
    
    Attributes:
        message: Primary message in the response
        metadata: Additional metadata about the response
        stop_reason: Why the agent stopped (tool_use, end_turn, etc.)
        raw_response: Raw response from the API
        routing: List of routing instructions from this response
    """
    message: Message
    metadata: Dict[str, Any] = field(default_factory=dict)
    stop_reason: Optional[str] = None
    raw_response: Any = None
    routing: List[RoutingInstruction] = field(default_factory=list)

    def has_text(self) -> bool:
        """Check if this response has text content."""
        return self.message.has_text()
    
    def is_using_tools(self) -> bool:
        """Check if this response is using tools."""
        return self.stop_reason == "tool_use" and self.message.has_tool_calls()

    def get_text_content(self) -> str:
        """Get the primary text content of this response."""
        return self.message.get_text()

    def get_tool_use_blocks(self) -> List[ToolCall]:
        """Get the tool use blocks in this response."""
        return self.message.get_tool_calls()

@dataclass
class AgentMetric:
    """
    Metrics for an agent execution.
    
    Attributes:
        agent_name: Name of the agent
        tokens_used: Total tokens used
        input_tokens: Tokens used in the prompt
        output_tokens: Tokens used in the completion
        execution_time: Time taken to execute
        tools_used: List of tools used
    """
    agent_name: str
    tokens_used: int
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    tools_used: List[str] = field(default_factory=list)

@dataclass
class AgentConfig:
    """
    Configuration for an agent.
    
    Attributes:
        name: Name of the agent
        model: Model to use
        system_prompt: System prompt to use
        tools: List of tools available to this agent
        max_tokens: Maximum tokens for this agent
        temperature: Temperature setting
    """
    name: AgentType
    model: str
    system_prompt: Optional[str] = None
    system_prompt_file: Optional[str] = None
    tools: List[Tool] = field(default_factory=list)
    description: Optional[str] = None
    persona_config: Optional[List[str]] = None
    emotion_block: bool = False
    max_tokens: int = 4000
    temperature: float = 0.7