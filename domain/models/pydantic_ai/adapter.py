"""
Adapter module for converting between our domain models and PydanticAI models.

This module provides functions and classes to facilitate the transition between
the existing model architecture and PydanticAI's components.
"""

import datetime
from typing import Any, Dict, List, Optional, Sequence, Union

import pydantic_ai
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.tools import RunContext

# Import legacy domain models
from domain.models.agent import AgentConfig as LegacyAgentConfig
from domain.models.agent import AgentResponse as LegacyAgentResponse
from domain.models.content import MessageContent as LegacyMessageContent
from domain.models.content import ToolCall as LegacyToolCall
from domain.models.content import ToolResponse as LegacyToolResponse
from domain.models.conversation import Conversation as LegacyConversation
from domain.models.enums import ContentType as LegacyContentType
from domain.models.messages import Message as LegacyMessage
from domain.models.routing import RoutingInstruction as LegacyRoutingInstruction
from domain.models.tool import Tool as LegacyTool


class PAIAdapter:
    """
    Adapter for converting between domain models and PydanticAI models.

    This adapter provides methods to convert back and forth between our
    existing domain models and the PydanticAI model structures.
    """

    @staticmethod
    def create_agent_from_config(config: LegacyAgentConfig, system_prompt: str) -> Agent:
        """
        Create a PydanticAI Agent from our legacy agent configuration.

        Args:
            config: Our legacy agent configuration
            system_prompt: Compiled system prompt to use

        Returns:
            pydantic_ai.Agent: A configured PydanticAI agent
        """
        # Create a basic agent with our configuration
        agent = Agent(
            model=f"anthropic:{config.model}",  # Use anthropic provider by default
            name=config.name.value if hasattr(config.name, "value") else str(config.name),
            system_prompt=system_prompt,
            # We'll add tools separately
        )

        # PydanticAI agents need additional setup for tools
        # This will be handled separately since tools need to be converted to functions

        return agent

    @staticmethod
    def convert_message_to_pai(message: LegacyMessage) -> ModelMessage:
        """
        Convert our domain message to PydanticAI message format.

        Args:
            message: Our domain Message object

        Returns:
            ModelMessage: PydanticAI representation of the message
        """
        parts = []

        # Process content items based on type
        for item in message.content:
            if item.type == LegacyContentType.TEXT:
                parts.append(TextPart(content=item.text or ""))

            elif item.type == LegacyContentType.TOOL_CALL and item.tool_call:
                # Convert to PydanticAI ToolCallPart
                tool_call = ToolCallPart(
                    tool_name=item.tool_call.tool_name,
                    args=item.tool_call.tool_input,
                    tool_call_id=item.tool_call.tool_id,
                )
                parts.append(tool_call)

            elif item.type == LegacyContentType.TOOL_RESULT and item.tool_result:
                # Convert to PydanticAI ToolReturnPart
                tool_result = ToolReturnPart(
                    tool_name=item.tool_result.type,
                    content=item.tool_result.content,
                    tool_call_id=item.tool_result.tool_id,
                    timestamp=datetime.datetime.now(),
                )
                parts.append(tool_result)

        # Create a PydanticAI ModelMessage based on role
        if message.role == "user":
            return ModelRequest(parts=[UserPromptPart(content=message.get_text())])
        elif message.role == "system":
            # Convert system message to system prompt part
            return ModelRequest(parts=[SystemPromptPart(content=message.get_text())])
        else:  # assistant
            return ModelResponse(parts=parts, model_name="claude-sonnet-4-5")

    @staticmethod
    def convert_conversation_to_pai_history(conversation: LegacyConversation) -> List[ModelMessage]:
        """
        Convert our Conversation to PydanticAI message history.

        Args:
            conversation: Our domain Conversation object

        Returns:
            List[ModelMessage]: PydanticAI message history
        """
        return [PAIAdapter.convert_message_to_pai(msg) for msg in conversation.messages]

    @staticmethod
    def convert_pai_message_to_legacy(message: ModelMessage) -> LegacyMessage:
        """
        Convert a PydanticAI message to our domain Message format.

        Args:
            message: PydanticAI ModelMessage object

        Returns:
            Message: Our domain Message representation
        """
        content_items = []

        # Determine the role
        if isinstance(message, ModelRequest):
            role = "user"
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    if isinstance(part.content, str):
                        content_items.append(LegacyMessageContent.make_text(part.content))
                    else:
                        # Handle multi-content user messages (e.g., text + image)
                        for content_item in part.content:
                            if isinstance(content_item, str):
                                content_items.append(LegacyMessageContent.make_text(content_item))

                elif isinstance(part, SystemPromptPart):
                    role = "system"
                    content_items.append(LegacyMessageContent.make_text(part.content))

        elif isinstance(message, ModelResponse):
            role = "assistant"
            for part in message.parts:
                if isinstance(part, TextPart):
                    content_items.append(LegacyMessageContent.make_text(part.content))

                elif isinstance(part, ToolCallPart):
                    # Convert to our ToolCall format
                    tool_call = LegacyToolCall(
                        tool_name=part.tool_name,
                        tool_input=part.args_as_dict(),
                        tool_id=part.tool_call_id,
                    )
                    content_items.append(LegacyMessageContent.make_tool_call(tool_call))

                elif isinstance(part, ToolReturnPart):
                    # Convert to our ToolResponse format
                    tool_result = LegacyToolResponse(
                        tool_id=part.tool_call_id,
                        content=part.content,
                        is_error=False,  # PydanticAI doesn't have a direct error flag
                    )
                    content_items.append(LegacyMessageContent.make_tool_result(tool_result))

        # Create our legacy Message with the appropriate content
        return LegacyMessage(role=role, content=content_items)


# Function decorators to help with tool conversion
def legacy_tool_to_pai_function(tool: LegacyTool):
    """
    Convert a legacy Tool to a PydanticAI function tool.

    This decorator helps convert our existing Tool objects to functions that
    can be registered with PydanticAI agents using @agent.tool.

    Args:
        tool: Our legacy Tool object

    Returns:
        Callable: A function that can be registered with PydanticAI
    """

    def wrapper(ctx: RunContext, **kwargs):
        """
        Function wrapper for legacy tool.

        Args:
            ctx: PydanticAI run context
            **kwargs: Tool parameters

        Returns:
            Any: Tool execution result
        """
        # Execute the legacy tool handler with the provided arguments
        return tool.handler(kwargs)

    # Set attributes to match the original tool
    wrapper.__name__ = tool.name
    wrapper.__doc__ = tool.description

    return wrapper
