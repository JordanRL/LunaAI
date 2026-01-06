from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from domain.models.agent import AgentConfig, AgentResponse
from domain.models.content import MessageContent, ToolCall, ToolResponse
from domain.models.conversation import Conversation
from domain.models.messages import Message


class BaseAdapter(ABC):
    """Base adapter interface for LLM API integrations."""

    @abstractmethod
    def __init__(self, api_key: str):
        """Initialize the adapter with API credentials."""
        pass

    @abstractmethod
    def send_message(
        self,
        system_prompt: str,
        message: Union[str, MessageContent, List[MessageContent], Message],
        history: Conversation,
        agent: AgentConfig,
    ) -> Any:
        """
        Send a message to the LLM service.

        Args:
            system_prompt: The system prompt
            message: The message to send
            history: Conversation history
            agent: Agent configuration

        Returns:
            Raw API response
        """
        pass

    @abstractmethod
    def process_response(self, response: Any, agent: AgentConfig) -> AgentResponse:
        """
        Process raw API response into standard AgentResponse format.

        Args:
            response: Raw API response
            agent: Agent configuration

        Returns:
            AgentResponse: Processed response
        """
        pass

    def convert_tool_schema(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tool schema to the provider-specific format.

        Args:
            tool_schema: The tool schema in Luna's format

        Returns:
            Dict: Tool schema in provider-specific format
        """
        # Default implementation returns the schema unchanged
        # Subclasses should override this method if needed
        return tool_schema

    def format_tool_result(self, tool_response: ToolResponse) -> Any:
        """
        Format a tool result for the provider-specific API.

        Args:
            tool_response: The tool response from Luna's internal format

        Returns:
            Any: Tool result in provider-specific format
        """
        # Default implementation returns a standard format
        # Subclasses should override this method
        return {
            "tool_call_id": tool_response.tool_id,
            "content": str(tool_response.content),
        }

    def convert_message_to_api_format(self, message: Message) -> Any:
        """
        Convert a Luna message to the provider-specific format.

        Args:
            message: Luna message to convert

        Returns:
            Any: Message in provider-specific format
        """
        # Default implementation - to be overridden
        return message.to_dict()

    def convert_history_to_api_format(self, messages: List[Message]) -> List[Any]:
        """
        Convert Luna message history to provider-specific format.

        Args:
            messages: List of Luna Message objects

        Returns:
            List: Messages in provider-specific format
        """
        # Default implementation - to be overridden
        return [self.convert_message_to_api_format(msg) for msg in messages]
