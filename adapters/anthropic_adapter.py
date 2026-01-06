"""
Anthropic API adapter for Luna.

This module provides an adapter for interacting with Anthropic's API.
"""

from typing import Any, Dict, List, Optional, Union

import anthropic
from anthropic.types import Message as AnthropicMessage
from anthropic.types import TextBlock, ToolUseBlock

from adapters.base_adapter import BaseAdapter
from domain.models.agent import AgentConfig, AgentResponse
from domain.models.content import MessageContent, ToolCall, ToolResponse
from domain.models.conversation import Conversation
from domain.models.enums import ContentType
from domain.models.messages import Message
from domain.models.routing import RoutingInstruction


class AnthropicAdapter(BaseAdapter):
    """
    Adapter for interacting with Anthropic's API.

    This adapter handles API calls, message formatting, and response parsing.
    """

    def __init__(self, api_key: str):
        """
        Initialize the adapter.

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def send_message(
        self,
        system_prompt: str,
        message: Union[str, MessageContent, List[MessageContent], Message],
        history: Conversation,
        agent: AgentConfig,
    ) -> AnthropicMessage:
        """
        Send a message using Anthropic's API.

        Args:
            system_prompt: System prompt for the message being sent (already compiled)
            message: Message to send (string, MessageContent, list of MessageContent, or Message)
            history: Conversation history for the message
            agent: Agent configuration

        Returns:
            AnthropicMessage: Response from the model
        """
        # The system_prompt is already compiled by the time it gets here,
        # so we don't need to do any token replacement at this level

        api_request = {
            "system": system_prompt,
            "messages": self.convert_history_to_api_format(history.messages),
            "model": agent.model,
            "max_tokens": agent.max_tokens,
            "temperature": agent.temperature,
            "tools": [self.convert_tool_schema(tool.to_api_schema()) for tool in agent.tools],
        }

        # Prepare the message based on its type
        if isinstance(message, str):
            # Create a simple text message
            message_obj = Message.user(message)
            api_request["messages"].append(self.convert_message_to_api_format(message_obj))
        elif isinstance(message, MessageContent):
            # Create a message with a single content item
            message_obj = Message(role="user", content=[message])
            api_request["messages"].append(self.convert_message_to_api_format(message_obj))
        elif isinstance(message, list) and all(
            isinstance(item, MessageContent) for item in message
        ):
            # Create a message with multiple content items
            message_obj = Message(role="user", content=message)
            api_request["messages"].append(self.convert_message_to_api_format(message_obj))
        elif isinstance(message, Message):
            # Use the message directly
            api_request["messages"].append(self.convert_message_to_api_format(message))
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

        # Make the API call
        api_response = self.client.messages.create(**api_request)

        return api_response

    def process_response(self, response: AnthropicMessage, agent: AgentConfig) -> AgentResponse:
        """
        Process a raw API response into an AgentResponse.

        Args:
            response: Raw API response
            agent: Agent configuration

        Returns:
            AgentResponse: Processed response
        """
        primary_text = ""
        tool_calls = []
        content_blocks = []

        # Convert each content block to our internal MessageContent format
        for content_item in response.content:
            if isinstance(content_item, TextBlock):
                # Create text content
                text = content_item.text
                if primary_text == "":  # Store the first text block as primary text
                    primary_text = text
                content_blocks.append(MessageContent.make_text(text))

            elif isinstance(content_item, ToolUseBlock):
                # Convert the input object to a dictionary if needed
                tool_input = content_item.input

                # If input has a __dict__ attribute (like an Anthropic object), convert it to a regular dict
                if hasattr(tool_input, "__dict__"):
                    tool_input = tool_input.__dict__
                elif hasattr(tool_input, "items"):
                    # For other dict-like objects, convert to regular dict
                    tool_input = {k: v for k, v in tool_input.items()}

                # Create tool call content and extract ToolCall for processing
                tool_call = ToolCall(
                    tool_name=content_item.name,
                    tool_id=content_item.id,
                    tool_input=tool_input,
                )
                tool_calls.append(tool_call)

                # Store the tool call content
                content_blocks.append(MessageContent.make_tool_call(tool_call=tool_call))

        # Create a complete message with all content blocks
        message = Message(role="assistant", content=content_blocks)

        # Extract routing instructions from any tool calls
        routing_instructions = self.extract_routing_instructions(tool_calls=tool_calls, agent=agent)

        # Create the agent response
        agent_response = AgentResponse(
            message=message,
            stop_reason=response.stop_reason,
            raw_response=response,
            routing=routing_instructions,
        )

        return agent_response

    def extract_routing_instructions(
        self, tool_calls: List[ToolCall], agent: AgentConfig
    ) -> List[RoutingInstruction]:
        """
        Extract routing instructions from a response.

        Args:
            tool_calls: API response
            agent: Agent configuration

        Returns:
            List[RoutingInstruction]: Extracted routing instructions
        """
        return [
            RoutingInstruction(source_agent=agent.name, tool_call=tool_call)
            for tool_call in tool_calls
        ]

    def convert_message_to_api_format(self, message: Message) -> Dict[str, Any]:
        """
        Convert a Luna message to Anthropic's format.

        For Anthropic, this uses message.to_dict() directly since our
        internal Message structure is based on Anthropic's format.

        Args:
            message: Luna message to convert

        Returns:
            Dict: Message in Anthropic format
        """
        return message.to_dict()

    def convert_history_to_api_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert Luna message history to Anthropic format.

        Args:
            messages: List of Luna Message objects

        Returns:
            List: Messages in Anthropic format
        """
        return [self.convert_message_to_api_format(msg) for msg in messages]

    def convert_tool_schema(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tool schema to Anthropic's format.

        Anthropic's format matches our internal format, so this returns the schema unchanged.

        Args:
            tool_schema: The tool schema in Luna's format

        Returns:
            Dict: Tool schema in Anthropic format
        """
        return tool_schema

    def format_tool_result(self, tool_response: ToolResponse) -> Dict[str, Any]:
        """
        Format a tool result for Anthropic's API.

        Anthropic expects tool_result content to be a string or content blocks.

        Args:
            tool_response: The tool response from Luna's internal format

        Returns:
            Dict: Tool result in Anthropic format
        """
        content = tool_response.content

        # Ensure content is a string or content blocks list
        if not isinstance(content, str) and not isinstance(content, list):
            # Convert to string using JSON if possible
            try:
                import json

                content = json.dumps(content)
            except:
                # Fall back to string representation
                content = str(content)

        result = {"type": "tool_result", "tool_use_id": tool_response.tool_id, "content": content}

        # Add is_error flag if needed
        if tool_response.is_error:
            result["is_error"] = True

        return result
