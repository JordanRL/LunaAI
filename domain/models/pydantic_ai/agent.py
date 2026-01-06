from dataclasses import field
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from pydantic_ai.agent import Agent

from domain.models.pydantic_ai.content import ToolCall
from domain.models.pydantic_ai.enums import AgentType
from domain.models.pydantic_ai.messages import Message
from domain.models.pydantic_ai.routing import RoutingInstruction
from domain.models.pydantic_ai.tool import Tool


class AgentResponse(BaseModel):
    """
    Response from an agent execution.

    This model represents the result of executing an agent,
    including the message content and any routing instructions.

    Attributes:
        message: Primary message in the response
        metadata: Additional metadata about the response
        stop_reason: Why the agent stopped (tool_use, end_turn, etc.)
        raw_response: Raw response from the API
        routing: List of routing instructions from this response
    """

    message: Message
    metadata: Dict[str, Any] = Field(default_factory=dict)
    stop_reason: Optional[str] = None
    raw_response: Any = None
    routing: List[RoutingInstruction] = Field(default_factory=list)

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

    def model_dump_usage(self) -> Dict[str, Any]:
        """Get usage information from the response."""
        if self.raw_response and hasattr(self.raw_response, "usage"):
            return {
                "prompt_tokens": getattr(self.raw_response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(self.raw_response.usage, "completion_tokens", 0),
                "total_tokens": getattr(self.raw_response.usage, "total_tokens", 0),
            }
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class AgentMetric(BaseModel):
    """
    Metrics for an agent execution.

    This model tracks performance metrics for an agent execution,
    including token usage and execution time.

    Attributes:
        agent_name: Name of the agent
        tokens_used: Total tokens used
        input_tokens: Tokens used in the prompt
        output_tokens: Tokens used in the completion
        execution_time: Time taken to execute
        tools_used: List of tools used
    """

    agent_name: str
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    execution_time: float = 0.0
    tools_used: List[str] = Field(default_factory=list)

    @classmethod
    def from_response(
        cls, agent_name: str, response: AgentResponse, execution_time: float
    ) -> "AgentMetric":
        """Create metrics from an agent response."""
        usage = response.model_dump_usage()
        tools_used = [tool.tool_name for tool in response.get_tool_use_blocks()]

        return cls(
            agent_name=agent_name,
            tokens_used=usage.get("total_tokens", 0),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            execution_time=execution_time,
            tools_used=tools_used,
        )


class AgentConfig(BaseModel):
    """
    Configuration for an agent.

    This model defines the configuration for an agent, including
    the model to use, available tools, and other settings.

    Attributes:
        name: Name of the agent
        model: Model to use
        system_prompt: System prompt to use
        tools: List of tools available to this agent
        max_tokens: Maximum tokens for this agent
        temperature: Temperature setting
        features: Feature flags controlling what content is included in prompts
    """

    name: AgentType
    model: str
    system_prompt: Optional[str] = None
    system_prompt_file: Optional[str] = None
    tools: List[Tool] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    features: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = 4000
    temperature: float = 0.7

    def model_validate_custom(self) -> None:
        """Validate that required features exist."""
        if not self.features:
            raise ValueError("Features dictionary is required in agent config")

        if "persona_config" not in self.features:
            raise ValueError("persona_config is required in features")

        if "cognitive" not in self.features:
            raise ValueError("cognitive flag is required in features")

        if self.features["cognitive"] and "cognitive_structure" not in self.features:
            raise ValueError("cognitive_structure is required when cognitive is true")

    def to_pydantic_ai_config(self) -> Dict[str, Any]:
        """Convert to PydanticAI agent configuration."""
        return {
            "name": self.name.value,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "tools": [tool.handler for tool in self.tools],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
