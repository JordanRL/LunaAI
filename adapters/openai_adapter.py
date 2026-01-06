"""
OpenAI API adapter for Luna.

This module provides an adapter for interacting with OpenAI's API.
"""

import json
from typing import Any, Dict, List, Optional, Union

import openai
from openai.types.chat import ChatCompletion

from adapters.base_adapter import BaseAdapter
from domain.models.agent import AgentConfig, AgentResponse
from domain.models.content import MessageContent, ToolCall, ToolResponse
from domain.models.conversation import Conversation
from domain.models.enums import ContentType
from domain.models.messages import Message
from domain.models.routing import RoutingInstruction


class OpenAIAdapter(BaseAdapter):
    """
    Adapter for interacting with OpenAI's API.

    This adapter handles API calls, message formatting, and response parsing.
    """

    def __init__(self, api_key: str):
        """
        Initialize the adapter.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=self.api_key)

    def send_message(
        self,
        system_prompt: str,
        message: Union[str, MessageContent, List[MessageContent], Message],
        history: Conversation,
        agent: AgentConfig,
    ) -> ChatCompletion:
        """
        Send a message using OpenAI's API.

        Args:
            system_prompt: System prompt for the message being sent (already compiled)
            message: Message to send (string, MessageContent, list of MessageContent, or Message)
            history: Conversation history for the message
            agent: Agent configuration

        Returns:
            ChatCompletion: Response from the model
        """
        # Convert history to OpenAI format
        openai_messages = self.convert_history_to_api_format(history.messages)

        # Add system message at the beginning
        openai_messages.insert(0, {"role": "system", "content": system_prompt})

        # Prepare the new message based on its type
        openai_message = None
        if isinstance(message, str):
            openai_message = {"role": "user", "content": message}
        elif isinstance(message, MessageContent):
            openai_message = self.format_message_content(message)
        elif isinstance(message, list) and all(
            isinstance(item, MessageContent) for item in message
        ):
            # Convert list of MessageContent to a single OpenAI message
            openai_message = self.format_message_content_list(message)
        elif isinstance(message, Message):
            openai_message = self.convert_message_to_api_format(message)
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

        # Add the new message to messages
        if openai_message:
            openai_messages.append(openai_message)

        # Prepare tools if available
        tools = None
        if agent.tools:
            tools = [self.convert_tool_schema(tool.to_api_schema()) for tool in agent.tools]

        # Prepare API call parameters
        api_params = {
            "model": agent.model,
            "messages": openai_messages,
        }

        # Handle O3 models differently - they don't support temperature or max_tokens
        if not agent.model.startswith("o3"):
            api_params["temperature"] = agent.temperature
            api_params["max_tokens"] = agent.max_tokens
        else:
            # O3 models use max_completion_tokens instead of max_tokens
            api_params["max_completion_tokens"] = agent.max_tokens

        # Add tools if available
        if tools:
            api_params["tools"] = tools

        # Make the API call
        api_response = self.client.chat.completions.create(**api_params)

        return api_response

    def process_response(self, response: ChatCompletion, agent: AgentConfig) -> AgentResponse:
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

        # Process the first choice
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            message = choice.message

            # Process text content
            if message.content:
                text = message.content
                primary_text = text
                content_blocks.append(MessageContent.make_text(text))

            # Process tool calls if available
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    # Extract tool call information
                    tool_name = tool_call.function.name
                    tool_id = tool_call.id
                    tool_input = tool_call.function.arguments

                    # Try to parse JSON string to dict
                    try:
                        tool_input = json.loads(tool_input)
                    except:
                        # If parsing fails, keep it as string
                        pass

                    # Create tool call object
                    tc = ToolCall(
                        tool_name=tool_name,
                        tool_id=tool_id,
                        tool_input=tool_input,
                    )
                    tool_calls.append(tc)
                    content_blocks.append(MessageContent.make_tool_call(tool_call=tc))

        # Create a complete message with all content blocks
        message = Message(role="assistant", content=content_blocks)

        # Extract routing instructions from any tool calls
        routing_instructions = self.extract_routing_instructions(tool_calls=tool_calls, agent=agent)

        # Determine stop reason based on OpenAI's finish_reason
        stop_reason = "stop"
        if response.choices and len(response.choices) > 0:
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "tool_calls":
                stop_reason = "tool_use"

        # Create the agent response
        agent_response = AgentResponse(
            message=message,
            stop_reason=stop_reason,
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
            tool_calls: List of tool calls
            agent: Agent configuration

        Returns:
            List[RoutingInstruction]: Extracted routing instructions
        """
        return [
            RoutingInstruction(source_agent=agent.name, tool_call=tool_call)
            for tool_call in tool_calls
        ]

    def convert_history_to_api_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert Luna message history to OpenAI format.

        Args:
            messages: List of Luna Message objects

        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []

        for msg in messages:
            openai_messages.append(self.convert_message_to_api_format(msg))

        return openai_messages

    def convert_message_to_api_format(self, message: Message) -> Dict[str, Any]:
        """
        Convert a Luna message to OpenAI format.

        This handles the different message types and converts them to OpenAI's
        expected format, which is different from our internal format.

        Args:
            message: Luna message to convert

        Returns:
            Dict: Message in OpenAI format
        """
        # Map Luna roles to OpenAI roles
        role = message.role

        # Simple text messages
        if message.has_text() and not message.has_tool_calls() and not message.has_tool_results():
            return {"role": role, "content": message.get_text()}

        # Messages with tool calls (assistant)
        if message.has_tool_calls() and role == "assistant":
            message_dict = {
                "role": role,
                "content": message.get_text() if message.has_text() else None,
                "tool_calls": [],
            }

            for tool_call in message.get_tool_calls():
                message_dict["tool_calls"].append(
                    {
                        "id": tool_call.tool_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.tool_name,
                            "arguments": json.dumps(tool_call.tool_input),
                        },
                    }
                )

            return message_dict

        # Messages with tool results (user)
        if message.has_tool_results() and role == "user":
            # OpenAI requires each tool result to be a separate message with "tool" role
            # We'll just handle the first tool result for simplicity
            tool_results = message.get_tool_results()
            if tool_results:
                return self.format_tool_result(tool_results[0])

        # Default handling for other cases
        return {"role": role, "content": message.get_text() or ""}

    def format_message_content(self, content: MessageContent) -> Dict[str, Any]:
        """Format a single MessageContent for OpenAI."""
        if content.type == ContentType.TEXT:
            return {"role": "user", "content": content.text or ""}

        elif content.type == ContentType.TOOL_RESULT and content.tool_result:
            return self.format_tool_result(content.tool_result)

        return {"role": "user", "content": ""}

    def format_message_content_list(self, content_list: List[MessageContent]) -> Dict[str, Any]:
        """Format a list of MessageContent items for OpenAI."""
        # For multiple content items, we need to handle them differently based on type
        # OpenAI doesn't support multiple content blocks like Anthropic
        # So we need to prioritize or combine them

        # Check if we have tool results
        tool_results = [item for item in content_list if item.type == ContentType.TOOL_RESULT]
        if tool_results and tool_results[0].tool_result:
            # Return just the first tool result
            return self.format_tool_result(tool_results[0].tool_result)

        # Otherwise, combine all text content
        text_items = [item for item in content_list if item.type == ContentType.TEXT]
        combined_text = " ".join([item.text or "" for item in text_items])
        return {"role": "user", "content": combined_text}

    def convert_tool_schema(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tool schema to OpenAI format.

        Args:
            tool_schema: The tool schema in Luna's format

        Returns:
            Dict: Tool schema in OpenAI format
        """
        return {
            "type": "function",
            "function": {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "parameters": tool_schema["input_schema"],
            },
        }

    def format_tool_result(self, tool_response: ToolResponse) -> Dict[str, Any]:
        """
        Format a tool result for OpenAI's API.

        OpenAI expects tool results as a "tool" role message with stringified content.

        Args:
            tool_response: The tool response from Luna's internal format

        Returns:
            Dict: Tool result in OpenAI format
        """
        content = tool_response.content

        # Ensure content is a string
        if not isinstance(content, str):
            # Convert to string using JSON if possible
            try:
                content = json.dumps(content)
            except:
                # Fall back to string representation
                content = str(content)

        return {"role": "tool", "tool_call_id": tool_response.tool_id, "content": content}
