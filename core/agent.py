"""
Agent implementation for Luna.

This module defines the agent implementation for Luna,
aligned with Anthropic's SDK patterns.
"""

from typing import Dict, List, Any, Optional, Union, Type
import time
from domain.models.agent import AgentResponse, AgentConfig
from domain.models.routing import RoutingInstruction
from domain.models.conversation import Conversation
from domain.models.messages import MessageContent, Message
from adapters.anthropic_adapter import AnthropicAdapter
from anthropic.types import Message as AnthropicMessage
from copy import deepcopy

class Agent:
    """
    Agent implementation aligned with Anthropic SDK patterns.
    
    This Agent class supports:
    - SDK-compatible message formatting
    - Multi-turn tool conversations
    - System prompts as separate parameters
    - Proper content block handling
    """
    
    def __init__(
            self, 
            config: AgentConfig,
            api_adapter: AnthropicAdapter
    ):
        """
        Initialize the agent.
        
        Args:
            config: Configuration for this agent
            api_adapter: Adapter for API calls
        """
        self.config = config
        self.name = config.name
        self.system_prompt = config.system_prompt
        self.tools = config.tools
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.api_adapter = api_adapter
        self.message_history = Conversation()
        
    def reset_history(self) -> None:
        """Reset the message history for a new user interaction."""
        self.message_history = Conversation()
        
    def execute(
            self,
            message: Union[str, MessageContent, List[MessageContent]],
            external_history: Optional[Conversation] = None
    ) -> AgentResponse:
        """
        Execute agent.
        
        Args:
            message: User message or specialized agent input
            external_history: Optional external context/history
            
        Returns:
            AgentResponse: Response from the agent
        """
        # Copy history
        history_copy = deepcopy(self.message_history)
        
        # Prepare message history
        if external_history.messages is not None and len(external_history.messages) > 0 :
            # Only include a limited number of recent messages to avoid context limits
            recent_external = external_history.messages[-5:] if len(external_history.messages) > 5 else external_history.messages
            history_copy.messages.extend(recent_external)

        # Create the current user message - can be a string, MessageContent, or Message
        # The API adapter will handle the appropriate conversion

        # Call the API adapter to execute the request
        start_time = time.time()
        response = self.api_adapter.send_message(
            system_prompt=self.system_prompt,
            message=message,
            history=history_copy,
            agent=self.config,
        )

        agent_response = self.api_adapter.process_response(response, self.config)
        
        # Add execution time
        response.execution_time = time.time() - start_time

        # Update persistent history with the user message
        if isinstance(message, str):
            user_message = Message.user(message)
        elif isinstance(message, MessageContent):
            user_message = Message(role="user", content=[message])
        elif isinstance(message, list) and all(isinstance(item, MessageContent) for item in message):
            user_message = Message(role="user", content=message)
        elif isinstance(message, Message):
            user_message = message
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")
            
        self.message_history.messages.append(user_message)
        
        # Add the response to the message history
        response_message = agent_response.message
        self.message_history.messages.append(response_message)
        
        return agent_response