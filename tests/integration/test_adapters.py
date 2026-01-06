"""
Integration tests for LLM adapters.

This module tests the different LLM adapters (Anthropic, OpenAI, Gemini)
to ensure they can be swapped seamlessly.
"""

import os
import unittest
from typing import Dict, List, Optional

from adapters.adapter_factory import AdapterFactory
from adapters.anthropic_adapter import AnthropicAdapter
from adapters.gemini_adapter import GeminiAdapter
from adapters.openai_adapter import OpenAIAdapter
from config.settings import get_api_keys
from domain.models.agent import AgentConfig
from domain.models.content import MessageContent
from domain.models.conversation import Conversation
from domain.models.enums import AgentType
from domain.models.messages import Message
from domain.models.tool import Tool, ToolRegistry


class TestAdapters(unittest.TestCase):
    """Test cases for LLM adapters."""

    def setUp(self):
        """Set up test environment."""
        self.api_keys = get_api_keys()

        # Simple calculator tool for testing
        self.calculator_tool = Tool(
            name="calculator",
            description="A simple calculator that can add, subtract, multiply, and divide.",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The operation to perform.",
                    },
                    "a": {"type": "number", "description": "The first number."},
                    "b": {"type": "number", "description": "The second number."},
                },
                "required": ["operation", "a", "b"],
            },
            handler=self.calculator_handler,
        )

        # Set up tool registry
        self.tools = ToolRegistry()
        self.tools.register(self.calculator_tool)

        # Base prompt for testing
        self.system_prompt = """You are a helpful AI assistant. Your task is to help users with
        their questions and perform calculations when needed."""

        # Test message
        self.test_message = "What is 2 + 2?"

        # Create a basic conversation
        self.conversation = Conversation()
        self.conversation.add_user_message("Hello, nice to meet you!")
        self.conversation.add_assistant_message(
            "Hello! Nice to meet you too. How can I help you today?"
        )

        # Basic agent config for testing
        self.agent_config = AgentConfig(
            name=AgentType.DISPATCHER,
            model="",  # Will be set in each test
            tools=[self.calculator_tool],
            allowed_tools=["calculator"],
            temperature=0.0,  # Use 0 for deterministic results in tests
            max_tokens=100,
            features={"persona_config": "test", "cognitive": False},
        )

    def calculator_handler(self, input_data: Dict) -> Dict:
        """Handle calculator operations."""
        operation = input_data.get("operation")
        a = input_data.get("a")
        b = input_data.get("b")

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

    @unittest.skipIf(not os.environ.get("ANTHROPIC_API_KEY"), "Anthropic API key not available")
    def test_anthropic_adapter(self):
        """Test Anthropic adapter."""
        adapter = AnthropicAdapter(api_key=self.api_keys.anthropic_api_key)

        # Set model for Anthropic
        self.agent_config.model = "claude-sonnet-4-5"

        # Test basic message
        response = adapter.send_message(
            system_prompt=self.system_prompt,
            message=self.test_message,
            history=self.conversation,
            agent=self.agent_config,
        )

        # Process the response
        agent_response = adapter.process_response(response, self.agent_config)

        # Check that we got a valid response
        self.assertIsNotNone(agent_response)
        self.assertTrue(agent_response.has_text())

        # The response should contain "4" somewhere
        self.assertIn("4", agent_response.get_text_content())

    @unittest.skipIf(not os.environ.get("OPENAI_API_KEY"), "OpenAI API key not available")
    def test_openai_adapter(self):
        """Test OpenAI adapter."""
        adapter = OpenAIAdapter(api_key=self.api_keys.openai_api_key)

        # Set model for OpenAI
        self.agent_config.model = "gpt-4o-mini"

        # Test basic message
        response = adapter.send_message(
            system_prompt=self.system_prompt,
            message=self.test_message,
            history=self.conversation,
            agent=self.agent_config,
        )

        # Process the response
        agent_response = adapter.process_response(response, self.agent_config)

        # Check that we got a valid response
        self.assertIsNotNone(agent_response)
        self.assertTrue(agent_response.has_text())

        # The response should contain "4" somewhere
        self.assertIn("4", agent_response.get_text_content())

    @unittest.skipIf(not os.environ.get("GEMINI_API_KEY"), "Gemini API key not available")
    def test_gemini_adapter(self):
        """Test Gemini adapter."""
        adapter = GeminiAdapter(api_key=self.api_keys.gemini_api_key)

        # Set model for Gemini
        self.agent_config.model = "gemini-1.5-pro"

        # Test basic message
        response = adapter.send_message(
            system_prompt=self.system_prompt,
            message=self.test_message,
            history=self.conversation,
            agent=self.agent_config,
        )

        # Process the response
        agent_response = adapter.process_response(response, self.agent_config)

        # Check that we got a valid response
        self.assertIsNotNone(agent_response)
        self.assertTrue(agent_response.has_text())

        # The response should contain "4" somewhere
        self.assertIn("4", agent_response.get_text_content())

    @unittest.skipIf(
        not (
            os.environ.get("ANTHROPIC_API_KEY")
            and os.environ.get("OPENAI_API_KEY")
            and os.environ.get("GEMINI_API_KEY")
        ),
        "Not all API keys available",
    )
    def test_adapter_factory(self):
        """Test the adapter factory."""
        # Test Anthropic
        anthropic_adapter = AdapterFactory.create(
            provider="anthropic", api_key=self.api_keys.anthropic_api_key
        )
        self.assertIsInstance(anthropic_adapter, AnthropicAdapter)

        # Test OpenAI
        openai_adapter = AdapterFactory.create(
            provider="openai", api_key=self.api_keys.openai_api_key
        )
        self.assertIsInstance(openai_adapter, OpenAIAdapter)

        # Test Gemini
        gemini_adapter = AdapterFactory.create(
            provider="gemini", api_key=self.api_keys.gemini_api_key
        )
        self.assertIsInstance(gemini_adapter, GeminiAdapter)


if __name__ == "__main__":
    unittest.main()
