#!/usr/bin/env python3
"""
Compare the behavior of different LLM adapters.

This script tests all three adapters (Anthropic, OpenAI, Gemini) with the same input
and tools to validate they work correctly with the same interface.
"""

import json
import os
import sys
import time
from typing import Any, Callable, Dict, List

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.anthropic_adapter import AnthropicAdapter
from adapters.base_adapter import BaseAdapter
from adapters.gemini_adapter import GeminiAdapter
from adapters.openai_adapter import OpenAIAdapter
from config.settings import get_api_keys
from domain.models.agent import AgentConfig
from domain.models.content import MessageContent, ToolResponse
from domain.models.conversation import Conversation
from domain.models.messages import Message
from domain.models.tool import Tool, ToolRegistry


# Create a simple calculator tool for testing
def calculator(args: Dict[str, Any]) -> Dict[str, Any]:
    """Simple calculator function that adds two numbers."""
    try:
        a = float(args.get("a", 0))
        b = float(args.get("b", 0))
        operation = args.get("operation", "add")

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {"error": "Cannot divide by zero"}
            result = a / b
        else:
            return {"error": f"Unknown operation: {operation}"}

        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


# Create a weather tool for testing
def weather(args: Dict[str, Any]) -> Dict[str, Any]:
    """Fake weather data for testing."""
    location = args.get("location", "").lower()

    weather_data = {
        "new york": {"temperature": 72, "conditions": "Partly cloudy"},
        "london": {"temperature": 62, "conditions": "Rainy"},
        "tokyo": {"temperature": 85, "conditions": "Sunny"},
        "sydney": {"temperature": 70, "conditions": "Clear"},
    }

    if location in weather_data:
        return {"location": location.title(), "data": weather_data[location]}
    else:
        return {"error": f"No weather data available for {location}"}


def main():
    # Get API keys from the project's settings module
    api_keys = get_api_keys()

    # Get API keys
    anthropic_api_key = api_keys.anthropic_api_key
    openai_api_key = api_keys.openai_api_key
    gemini_api_key = api_keys.gemini_api_key

    # Check if we have any valid keys
    valid_keys = {
        "anthropic": len(anthropic_api_key) > 10 and anthropic_api_key != "sk-ant-xxxx",
        "openai": len(openai_api_key) > 10 and openai_api_key != "sk-xxxx",
        "gemini": len(gemini_api_key) > 10 and gemini_api_key != "xxxx",
    }

    if not any(valid_keys.values()):
        print(
            "Error: No valid API keys found. Please set at least one of these in your environment:"
        )
        print("  - ANTHROPIC_API_KEY for testing the Anthropic adapter")
        print("  - OPENAI_API_KEY for testing the OpenAI adapter")
        print("  - GEMINI_API_KEY for testing the Gemini adapter")
        sys.exit(1)

    # Create tools
    calculator_tool = Tool(
        name="calculator",
        description="A calculator that can add, subtract, multiply, and divide two numbers.",
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "The first number"},
                "b": {"type": "number", "description": "The second number"},
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The operation to perform",
                },
            },
            "required": ["a", "b", "operation"],
        },
        handler=calculator,
    )

    weather_tool = Tool(
        name="weather",
        description="Gets the current weather for a location.",
        input_schema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for (city name)",
                },
            },
            "required": ["location"],
        },
        handler=weather,
    )

    # Create tool registry
    registry = ToolRegistry()
    registry.register(calculator_tool)
    registry.register(weather_tool)

    # Define test adapters
    adapters = {}
    agent_configs = {}

    # Create a basic features dictionary required by AgentConfig
    basic_features = {
        "persona_config": {
            "name": "Tester",
            "persona": "You are a helpful assistant for testing purposes.",
        },
        "cognitive": False,
        "cognitive_structure": {},
    }

    # Only create adapters for valid API keys
    if valid_keys["anthropic"]:
        adapters["anthropic"] = AnthropicAdapter(anthropic_api_key)
        agent_configs["anthropic"] = AgentConfig(
            name="anthropic_agent",
            model="claude-sonnet-4-5",
            max_tokens=1000,
            temperature=0.7,
            tools=[calculator_tool, weather_tool],
            features=basic_features.copy(),
        )

    if valid_keys["openai"]:
        adapters["openai"] = OpenAIAdapter(openai_api_key)
        agent_configs["openai"] = AgentConfig(
            name="openai_agent",
            model="gpt-4o-mini",
            max_tokens=1000,
            temperature=0.7,
            tools=[calculator_tool, weather_tool],
            features=basic_features.copy(),
        )

    if valid_keys["gemini"]:
        adapters["gemini"] = GeminiAdapter(gemini_api_key)
        agent_configs["gemini"] = AgentConfig(
            name="gemini_agent",
            model="gemini-2.0-flash",
            max_tokens=1000,
            temperature=0.7,
            tools=[calculator_tool, weather_tool],
            features=basic_features.copy(),
        )

    print(f"Testing {len(adapters)} adapters: {', '.join(adapters.keys())}")

    # Test system prompt
    system_prompt = """You are a helpful assistant. When asked about calculations or weather, please use the appropriate tool. Respond briefly and clearly."""

    # Initial conversation with a single message
    conversation = Conversation()
    conversation.add_message(Message.user("Hello, how are you?"))

    # Test each adapter with a simple chat message
    for adapter_name, adapter in adapters.items():
        print(f"\n--- Testing {adapter_name.upper()} Adapter (Text Message) ---")
        try:
            agent_config = agent_configs[adapter_name]
            message = "What's 234 + 345? Please use the calculator tool."

            start_time = time.time()
            raw_response = adapter.send_message(system_prompt, message, conversation, agent_config)
            response = adapter.process_response(raw_response, agent_config)
            end_time = time.time()

            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"Text response: {response.message.get_text()}")
            print(f"Has tool calls: {response.message.has_tool_calls()}")
            if response.message.has_tool_calls():
                print(f"Tool calls: {len(response.message.get_tool_calls())}")
                for tool_call in response.message.get_tool_calls():
                    print(f"  Tool: {tool_call.tool_name}")
                    print(f"  Inputs: {tool_call.tool_input}")

            # Test tool execution and sending results back
            if response.message.has_tool_calls():
                tool_calls = response.message.get_tool_calls()

                # Process first tool call
                if tool_calls:
                    tool_call = tool_calls[0]
                    tool = registry.get(tool_call.tool_name)

                    if tool:
                        # Execute tool
                        result = tool.safe_execute(tool_call.tool_input)
                        print(f"Tool result: {result}")

                        # Create tool response
                        tool_response = ToolResponse(tool_id=tool_call.tool_id, content=result)

                        # Format tool response for this adapter
                        formatted_response = adapter.format_tool_result(tool_response)
                        print(
                            f"Formatted tool response: {json.dumps(formatted_response, indent=2)}"
                        )

                        # Get the properly formatted tool result for this adapter
                        # The adapter already takes care of the correct format for each API

                        # Create a new conversation with the assistant's tool call
                        tool_conversation = Conversation()
                        # Add the greeting message
                        tool_conversation.add_message(Message.user("Hello, how are you?"))
                        # Add assistant's response with the greeting (if it exists)
                        if len(conversation.messages) > 1:
                            tool_conversation.add_message(conversation.messages[1])
                        # Add the calculation question
                        tool_conversation.add_message(Message.user(message))
                        # Add assistant's response with tool call
                        tool_conversation.add_message(response.message)

                        print(f"\n--- Sending tool result back to {adapter_name.upper()} ---")
                        # Use the Message.user_with_tool_result convenience method
                        # Each adapter will format it correctly in convert_message_to_api_format

                        # Ensure the content is properly serialized to a JSON string before sending
                        result_content = tool_response.content
                        if isinstance(result_content, dict):
                            result_content = json.dumps(result_content)

                        tool_result_message = Message.user_with_tool_result(
                            tool_id=tool_response.tool_id, result=result_content
                        )

                        # Debug: Print the message that's being sent, with details about the tool result content
                        message_dict = tool_result_message.to_dict()
                        print(f"\nDEBUG - Message being sent:")
                        print(f"Role: {message_dict.get('role')}")
                        print(f"Content length: {len(message_dict.get('content', []))}")
                        for idx, content_item in enumerate(message_dict.get("content", [])):
                            print(f"Content item {idx}: type={content_item.get('type')}")
                            if content_item.get("type") == "tool_result":
                                print(f"  tool_use_id: {content_item.get('tool_use_id')}")
                                print(f"  content type: {type(content_item.get('content'))}")
                                print(f"  content: {content_item.get('content')}")

                        raw_result_response = adapter.send_message(
                            system_prompt, tool_result_message, tool_conversation, agent_config
                        )
                        result_response = adapter.process_response(
                            raw_result_response, agent_config
                        )

                        print(f"Final response: {result_response.message.get_text()}")
        except Exception as e:
            print(f"Error with {adapter_name} adapter: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
