"""
Google Gemini API adapter for Luna.

This module provides an adapter for interacting with Google's Gemini API.
"""

import json
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types

from adapters.base_adapter import BaseAdapter
from domain.models.agent import AgentConfig, AgentResponse
from domain.models.content import MessageContent, ToolCall, ToolResponse
from domain.models.conversation import Conversation
from domain.models.enums import ContentType
from domain.models.messages import Message
from domain.models.routing import RoutingInstruction


class GeminiAdapter(BaseAdapter):
    """
    Adapter for interacting with Google's Gemini API.

    This adapter handles API calls, message formatting, and response parsing.
    """

    def __init__(self, api_key: str):
        """
        Initialize the adapter.

        Args:
            api_key: Google API key
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)

    def send_message(
        self,
        system_prompt: str,
        message: Union[str, MessageContent, List[MessageContent], Message],
        history: Conversation,
        agent: AgentConfig,
    ) -> types.GenerateContentResponse:
        """
        Send a message using Google's Gemini API.

        Args:
            system_prompt: System prompt for the message being sent (already compiled)
            message: Message to send (string, MessageContent, list of MessageContent, or Message)
            history: Conversation history for the message
            agent: Agent configuration

        Returns:
            Response from the model
        """
        # Convert history to Gemini format
        gemini_history = self.convert_history_to_api_format(history.messages)

        # Create model generation parameters
        generation_config = {
            "max_output_tokens": agent.max_tokens,
            "temperature": agent.temperature,
        }

        # Create tools configuration if available
        tools = None
        if agent.tools:
            tools = []
            for tool in agent.tools:
                # Convert our tool schema to Gemini's expected format
                tool_schema = self.convert_tool_schema(tool.to_api_schema())
                tools.append(tool_schema)

        # Get the appropriate model
        model = self.client.get_model(agent.model)

        # Prepare the message based on its type
        content = None
        if isinstance(message, str):
            content = message
        elif isinstance(message, MessageContent):
            content = self.format_message_content(message)
        elif isinstance(message, list) and all(
            isinstance(item, MessageContent) for item in message
        ):
            content = self.format_message_content_list(message)
        elif isinstance(message, Message):
            content = self.convert_message_to_api_format(message)
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

        # Add the new message to history
        if content and system_prompt:
            # Add system prompt to history if not already present
            sys_msg = {"role": "system", "content": system_prompt}

            # Add the content to history
            chat_session = [sys_msg] + gemini_history + [content]
        elif content:
            chat_session = gemini_history + [content]
        else:
            chat_session = gemini_history

        # Make the API call with history and tools
        if tools:
            api_response = model.generate_content(
                chat_session, generation_config=generation_config, tools=tools
            )
        else:
            api_response = model.generate_content(chat_session, generation_config=generation_config)

        return api_response

    def process_response(
        self, response: types.GenerateContentResponse, agent: AgentConfig
    ) -> AgentResponse:
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

        # Process text content
        if hasattr(response, "text") and response.text:
            text = response.text
            primary_text = text
            content_blocks.append(MessageContent.make_text(text))

        # Process function calls if available
        if hasattr(response, "function_calls") and response.function_calls:
            for function_call in response.function_calls:
                # Extract the function name and arguments
                name = function_call.get("name", "unknown_function")

                # Parse the arguments
                args = {}
                if hasattr(function_call, "args") and function_call.args:
                    args = function_call.args

                # Generate a unique ID for this tool call
                # Since Gemini doesn't provide IDs, we use the function name
                tool_id = name

                # Create a tool call
                tool_call = ToolCall(tool_name=name, tool_id=tool_id, tool_input=args)

                tool_calls.append(tool_call)
                content_blocks.append(MessageContent.make_tool_call(tool_call=tool_call))

        # Create a complete message with all content blocks
        message = Message(role="assistant", content=content_blocks)

        # Extract routing instructions from any tool calls
        routing_instructions = self.extract_routing_instructions(tool_calls=tool_calls, agent=agent)

        # Determine stop reason
        stop_reason = "stop" if not tool_calls else "tool_use"

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

    def convert_message_to_api_format(self, message: Message) -> Dict[str, Any]:
        """
        Convert a Luna message to Gemini's format.

        Args:
            message: Luna message to convert

        Returns:
            Dict: Message in Gemini format
        """
        # Map Luna roles to Gemini roles
        role = "user" if message.role == "user" else "model"

        # Handle text content
        if message.has_text():
            return {"role": role, "content": message.get_text()}

        # Handle tool results (from user to model)
        if message.has_tool_results() and message.role == "user":
            # Get first tool result
            tool_results = message.get_tool_results()
            if tool_results:
                result_content = self.format_tool_result(tool_results[0])
                # For Gemini, tool results are sent as user messages with the content
                return {"role": "user", "content": result_content}

        # Default to empty text message
        return {"role": role, "content": ""}

    def convert_history_to_api_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert Luna message history to Gemini format.

        Args:
            messages: List of Luna Message objects

        Returns:
            List: Messages in Gemini format
        """
        gemini_messages = []

        for msg in messages:
            # Convert the message
            gemini_msg = self.convert_message_to_api_format(msg)

            # Add it to history if not empty
            if gemini_msg:
                gemini_messages.append(gemini_msg)

        return gemini_messages

    def format_message_content(self, content: MessageContent) -> Dict[str, Any]:
        """Format a single MessageContent for Gemini."""
        if content.type == ContentType.TEXT:
            return {"role": "user", "content": content.text or ""}

        elif content.type == ContentType.TOOL_RESULT and content.tool_result:
            result_content = self.format_tool_result(content.tool_result)
            return {"role": "user", "content": result_content}

        # Default empty user message
        return {"role": "user", "content": ""}

    def format_message_content_list(self, content_list: List[MessageContent]) -> Dict[str, Any]:
        """Format a list of MessageContent items for Gemini."""
        # For multiple content items, combine text parts
        combined_text = ""

        # Check for tool results first
        for item in content_list:
            if item.type == ContentType.TOOL_RESULT and item.tool_result:
                # Just handle the first tool result
                result_content = self.format_tool_result(item.tool_result)
                return {"role": "user", "content": result_content}

        # If no tool results, combine text content
        for item in content_list:
            if item.type == ContentType.TEXT and item.text:
                if combined_text:
                    combined_text += "\n"
                combined_text += item.text

        # Return combined text
        return {"role": "user", "content": combined_text or ""}

    def convert_tool_schema(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a tool schema to Gemini's format.

        Args:
            tool_schema: The tool schema in Luna's format

        Returns:
            Dict: Tool schema in Gemini format
        """
        return {
            "name": tool_schema["name"],
            "description": tool_schema["description"],
            "parameters": tool_schema["input_schema"],
        }

    def format_tool_result(self, tool_response: ToolResponse) -> str:
        """
        Format a tool result for Gemini's API.

        Gemini expects function results as a simple string in the user message content.

        Args:
            tool_response: The tool response from Luna's internal format

        Returns:
            str: Tool result in Gemini format as a string
        """
        content = tool_response.content

        # Ensure content is properly formatted for Gemini
        if not isinstance(content, str):
            # Convert to string using JSON if possible
            try:
                content = json.dumps(content)
            except:
                # Fall back to string representation
                content = str(content)

        # Format the response as a simple string mentioning which function it's responding to
        formatted_result = f"The result from {tool_response.tool_id} is: {content}"

        return formatted_result
