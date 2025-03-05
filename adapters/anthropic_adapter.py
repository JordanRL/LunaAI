"""
Anthropic API adapter for Luna.

This module provides an adapter for interacting with Anthropic's API.
"""

from typing import Dict, List, Any, Optional, Union
from domain.models.agent import AgentResponse, AgentConfig
from domain.models.conversation import Conversation
from domain.models.messages import MessageContent, Message
from domain.models.enums import ContentType
from domain.models.routing import RoutingInstruction, ToolCall
import anthropic
from anthropic.types import Message as AnthropicMessage

class AnthropicAdapter:
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
            agent: AgentConfig
    ) -> AnthropicMessage:
        """
        Send a message using Anthropic's API.
        
        Args:
            system_prompt: System prompt for the message being sent
            message: Message to send (string, MessageContent, list of MessageContent, or Message)
            history: Conversation history for the message
            agent: Agent configuration
            
        Returns:
            AnthropicMessage: Response from the model
        """
        api_request = {
            "system": system_prompt,
            "messages": [msg.to_dict() for msg in history.messages],
            "model": agent.model,
            "max_tokens": agent.max_tokens,
            "temperature": agent.temperature,
            "tools": [tool.to_api_schema() for tool in agent.tools],
        }

        # Prepare the message based on its type
        if isinstance(message, str):
            # Create a simple text message
            message_obj = Message.user(message)
            api_request["messages"].append(message_obj.to_dict())
        elif isinstance(message, MessageContent):
            # Create a message with a single content item
            message_obj = Message(role="user", content=[message])
            api_request["messages"].append(message_obj.to_dict())
        elif isinstance(message, list) and all(isinstance(item, MessageContent) for item in message):
            # Create a message with multiple content items
            message_obj = Message(role="user", content=message)
            api_request["messages"].append(message_obj.to_dict())
        elif isinstance(message, Message):
            # Use the message directly
            api_request["messages"].append(message.to_dict())
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
            content_type = content_item.get("type")
            
            if content_type == "text":
                # Create text content
                text = content_item.get("text", "")
                if primary_text == "":  # Store the first text block as primary text
                    primary_text = text
                content_blocks.append(MessageContent.text(text))
                
            elif content_type == "tool_call":
                # Create tool call content and extract ToolCall for processing
                tool_call = ToolCall(
                    tool_name=content_item.get("name", ""),
                    tool_id=content_item.get("id", ""),
                    tool_input=content_item.get("input", {})
                )
                tool_calls.append(tool_call)
                
                # Store the tool call content
                content_blocks.append(MessageContent.tool_call(
                    name=content_item.get("name", ""),
                    input_data=content_item.get("input", {}),
                    tool_id=content_item.get("id", "")
                ))
        
        # Create a complete message with all content blocks
        message = Message(role="assistant", content=content_blocks)
        
        # Extract routing instructions from any tool calls
        routing_instructions = self.extract_routing_instructions(tool_calls=tool_calls, agent=agent)

        # Create the agent response
        agent_response = AgentResponse(
            message=message,
            tool_use_blocks=tool_calls,
            text_blocks=content_blocks,
            stop_reason=response.stop_reason,
            raw_response=response,
            routing=routing_instructions
        )

        return agent_response
    
    def extract_routing_instructions(self, tool_calls: List[ToolCall], agent: AgentConfig) -> List[RoutingInstruction]:
        """
        Extract routing instructions from a response.

        Args:
            tool_calls: API response
            agent: Agent configuration

        Returns:
            List[RoutingInstruction]: Extracted routing instructions
        """
        return [RoutingInstruction(source_agent=agent.name, tool_call=tool_call) for tool_call in tool_calls]