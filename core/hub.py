"""
Hub implementation for Luna.

This module defines the hub implementation for Luna's hub-based architecture,
where the dispatcher serves as the central coordinator for all agent communication.
"""

import datetime
import json
import sys
from typing import Any, Dict, List, Optional

from rich.pretty import Pretty
from rich.prompt import Prompt

from adapters.console_adapter import ConsoleAdapter
from config.settings import get_api_keys, get_app_config
from core.agent import Agent
from domain.models.agent import AgentResponse
from domain.models.content import MessageContent, ToolResponse
from domain.models.memory import EpisodicMemoryQuery, MemoryQuery
from domain.models.routing import RoutingInstruction
from domain.models.tool import ToolRegistry
from services.conversation_service import ConversationService
from services.emotion_service import EmotionService
from services.prompt_service import PromptService
from services.user_service import UserService


class LunaHub:
    """
    Central hub system for Luna's cognitive architecture.

    This implements the hub-and-spoke architecture where the dispatcher
    is the central coordinator for all inter-agent communication.
    """

    agents: Dict[str, Agent]
    tools: ToolRegistry
    execution_stats: Dict[str, Any]

    def __init__(
        self,
        console_adapter: ConsoleAdapter,
        conversation_service: ConversationService,
        emotion_service: EmotionService,
        prompt_service: PromptService,
        user_service: UserService,
        memory_service=None,
    ):
        """
        Initialize the Luna hub system.

        Args:
            console_adapter: Adapter for console I/O
            conversation_service: Service for managing conversation state
            emotion_service: Service for managing emotional state
            prompt_service: Service for managing system prompts
            user_service: Service for managing user information
            memory_service: Optional service for memory operations
        """
        self.execution_stats = {"total_tokens": 0, "total_time": 0, "requests": 0}

        # Adapters
        self.console_adapter = console_adapter

        # Services
        self.conversation_service = conversation_service
        self.emotion_service = emotion_service
        self.prompt_service = prompt_service
        self.user_service = user_service
        self.memory_service = memory_service

        self.app_config = get_app_config()

        # Load tools and agents
        self._load_tools()
        self._load_agents()

    def _load_agents(self) -> None:
        """
        Load all agent components from the system_prompts directory.

        For each directory in system_prompts, this method:
        1. Reads the agent.json file
        2. Uses PromptService to load and preprocess the system prompt
        3. Creates an AgentConfig object for the agent
        4. Creates an Agent instance using the AgentConfig
        5. Stores the Agent in self.agents dictionary with name as key
        """
        import json
        import os

        from adapters.anthropic_adapter import AnthropicAdapter
        from core.agent import Agent
        from domain.models.agent import AgentConfig
        from domain.models.enums import AgentType

        # Get the API key from environment
        api_keys = get_api_keys()
        api_adapter = AnthropicAdapter(api_key=api_keys.anthropic_api_key)

        self.agents = {}
        system_prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "system_prompts"
        )

        recent_memories = self.memory_service.retrieve_memories(
            EpisodicMemoryQuery(
                limit=5,
                user_id="Jordan",
            )
        )

        recent_memories_str = ""
        for memory in recent_memories:
            recent_memories_str = f"\n<MemoryJSON>\n{json.dumps(memory.to_document())}\n</MemoryJSON>\n{recent_memories_str}"

        created, user_profile, user_relationship = self.user_service.create_or_get_user(
            user_id="Jordan"
        )

        token_replacements = {
            "USER_PROFILE": user_profile.model_dump(mode="json"),
            "USER_RELATIONSHIP": user_relationship.model_dump(mode="json"),
            "RECENT_MEMORY": recent_memories_str,
        }

        # Iterate through directories in system_prompts
        for agent_dir in os.listdir(system_prompts_dir):
            agent_path = os.path.join(system_prompts_dir, agent_dir)

            # Skip if not a directory
            if not os.path.isdir(agent_path):
                continue

            # Check for required files
            agent_json_path = os.path.join(agent_path, "agent.json")

            # Skip if required files don't exist
            if not os.path.exists(agent_json_path):
                continue

            # Load agent.json
            with open(agent_json_path, "r") as file:
                agent_config_data = json.load(file)

            # Create AgentConfig object
            agent_name = agent_config_data.get("name")

            current_token_replacements = token_replacements.copy()

            if not agent_config_data.get("user_relationship"):
                del current_token_replacements["USER_RELATIONSHIP"]
            if not agent_config_data.get("recent_memory"):
                del current_token_replacements["RECENT_MEMORY"]

            try:
                # Load and preprocess the system prompt using PromptService
                self.prompt_service.load_raw_prompt(agent_name)
            except FileNotFoundError:
                # Skip this agent if no system prompt is found
                continue

            # Get tools for this agent
            tool_names = agent_config_data.get("tools", [])
            tools = []
            allowed_tools = []

            # After loading tools in _load_tools, populate the tools list
            if hasattr(self, "tools") and self.tools is not None:
                for tool_name in tool_names:
                    tool = self.tools.get(tool_name)
                    if tool:
                        allowed_tools.append(tool_name)
                        tools.append(tool)

            # Create AgentConfig
            agent_config = AgentConfig(
                name=AgentType(agent_name),
                model=agent_config_data.get("model", "claude-3-7-sonnet-latest"),
                tools=tools,
                allowed_tools=allowed_tools,
                max_tokens=agent_config_data.get("max_tokens", 4000),
                temperature=agent_config_data.get("temperature", 0.7),
                description=agent_config_data.get("description", None),
                persona_config=agent_config_data.get("persona_config", []),
            )

            system_prompt = self.prompt_service.preprocess_prompt(
                agent_config, current_token_replacements
            )
            agent_config.system_prompt = system_prompt

            # Create Agent instance
            agent = Agent(
                config=agent_config,
                api_adapter=api_adapter,
                prompt_service=self.prompt_service,
            )

            # Store in agents dictionary
            self.agents[agent_name] = agent

    def _load_tools(self) -> None:
        """
        Load all tools from the domain/tools directory.

        This method dynamically discovers and loads all tools defined in the
        domain/tools folder without requiring a hardcoded list. It then stores
        them in the self.tools property as an instance of the ToolRegistry class.

        If a memory service is provided during hub initialization, it will be
        assigned to all memory-related tools.
        """
        import importlib
        import inspect
        import pkgutil

        import domain.tools
        from domain.models.tool import Tool, ToolCategory, ToolRegistry

        # Initialize the tool registry
        self.tools = ToolRegistry()

        # Get the package directory for domain.tools
        for _, module_name, is_pkg in pkgutil.iter_modules(
            domain.tools.__path__, domain.tools.__name__ + "."
        ):
            if not is_pkg:  # Only process modules, not sub-packages
                # Import the module
                module = importlib.import_module(module_name)

                # Find all Tool classes in the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class and is a subclass of Tool but not Tool itself
                    if inspect.isclass(obj) and issubclass(obj, Tool) and obj is not Tool:
                        # Get the signature of the tool's __init__ method to check for service dependencies
                        init_signature = inspect.signature(obj.__init__)
                        init_params = {}

                        # Check for services in the constructor parameters
                        for param_name, param in init_signature.parameters.items():
                            if param_name == "self":
                                continue

                            # Check if parameter is a service we have
                            if param_name == "memory_service" and self.memory_service:
                                init_params[param_name] = self.memory_service
                            elif param_name == "emotion_service" and self.emotion_service:
                                init_params[param_name] = self.emotion_service
                            elif param_name == "user_service" and self.user_service:
                                init_params[param_name] = self.user_service
                            elif param_name == "conversation_service" and self.conversation_service:
                                init_params[param_name] = self.conversation_service
                            elif param_name == "prompt_service" and self.prompt_service:
                                init_params[param_name] = self.prompt_service

                        # Instantiate the tool with injected services
                        tool_instance = obj(**init_params)

                        # For backward compatibility, also check set_* methods
                        # This handles tools created before we updated the initialization method
                        if (
                            self.memory_service
                            and hasattr(tool_instance, "category")
                            and tool_instance.category == ToolCategory.MEMORY
                            and hasattr(tool_instance, "set_memory_service")
                            and "memory_service" not in init_params
                        ):
                            # Set the memory service
                            tool_instance.set_memory_service(self.memory_service)

                        # Register the tool in the registry
                        self.tools.register(tool_instance)

    def _handle_command(self, user_message: str) -> bool:
        """
        Handles basic commands.
        """
        if user_message == "/exit" or user_message == "/quit":
            return False
        return True

    def process_message(self, user_message: str, user_id: str) -> str:
        """
        Process a user message through the agent network.

        This uses the new execution and routing architecture:
        1. Execute dispatcher agent
        2. Process any routing instructions
        3. Return final formatted response

        Args:
            user_message: The user's input message
            user_id: The user's unique ID

        Returns:
            String with the final response
        """
        # Check for heartbeat message
        if user_message.startswith("[HEARTBEAT]"):
            return self._process_heartbeat(user_message, user_id)

        commands = self._handle_command(user_message)

        if not commands:
            exit("Time to quit. Goodbye!")

        # Get conversation ID
        conversation_id = self.conversation_service.get_conversation_id_by_user_id(user_id)
        if not conversation_id:
            conversation = self.conversation_service.create_conversation(user_id)
            conversation_id = conversation.conversation_id

        # Store user message in conversation
        self.conversation_service.add_user_message(
            conversation_id, MessageContent.make_text(user_message)
        )

        # Create context message for dispatcher
        context_message = self._build_context_message(user_message, user_id)

        # Execute dispatcher agent with token replacements
        dispatcher_response = self.execute_agent(
            agent_name="dispatcher",
            message=context_message,
            conversation_history=self.conversation_service.get_conversation(conversation_id),
        )

        # Process routing instructions if any
        if dispatcher_response.is_using_tools():
            for route in dispatcher_response.routing:
                dispatcher_response = self.execute_routing(routing=route, depth=0, max_depth=6)

        # Format final response with outputter
        formatted_content = self._prepare_output_content(user_message, dispatcher_response)

        # Execute outputter with the same token replacements
        outputter_response = self.execute_agent(
            agent_name="outputter",
            message=formatted_content,
        )

        final_response = outputter_response.message.content[-1]

        # Store assistant message in conversation
        self.conversation_service.add_assistant_message(conversation_id, final_response)

        # Decay emotional state
        self.emotion_service.decay()

        # Update user interaction stats
        self.user_service.update_interaction_stats(user_id)

        return outputter_response.message.get_text()

    def user_prompt(self):
        return Prompt().ask(
            prompt="[bold cyan]You>[/bold cyan] ", console=self.console_adapter.console
        )

    def execute_agent(
        self,
        agent_name: str,
        message: str | MessageContent | List[MessageContent],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        suppress_thinking: bool = False,
        token_replacements: Optional[Dict[str, str]] = None,
    ) -> AgentResponse:
        """
        Execute a specific agent with proper context management.

        Args:
            agent_name: Name of the agent to execute
            message: Input message for the agent
            conversation_history: Optional history to include
            suppress_thinking: Whether to suppress the thinking message for this agent
            token_replacements: Optional dictionary of token replacements to use for this agent's system prompt

        Returns:
            The final AgentResponse after all tool processing
        """
        if agent_name not in self.agents:
            # Return error response if agent not found
            raise ValueError(f"Agent {agent_name} not found")

        agent = self.agents[agent_name]
        token_replacements = token_replacements or {}

        # Fill in emotional state tokens if the agent needs it
        if agent.config.emotion_block:
            emotional_state = self.emotion_service.get_current_state()
            token_replacements["PAD_PLEASURE"] = emotional_state.pleasure.__str__()
            token_replacements["PAD_AROUSAL"] = emotional_state.arousal.__str__()
            token_replacements["PAD_DOMINANCE"] = emotional_state.dominance.__str__()
            token_replacements["PAD_DESCRIPTOR"] = self.emotion_service.get_emotion_label()

        # Compile the system prompt with dynamic token replacement
        compiled_prompt = self.prompt_service.compile_prompt(
            agent_name=agent_name,
            token_replacements=token_replacements,
        )

        # Update the agent's system prompt with the compiled version
        original_prompt = agent.config.system_prompt
        agent.config.system_prompt = compiled_prompt

        # Execute the agent with the updated system prompt
        agent_response = agent.execute(message, conversation_history)

        # Restore the original (preprocessed) system prompt
        agent.config.system_prompt = original_prompt

        if not suppress_thinking and agent_response.has_text():
            self.console_adapter.display_thinking(
                thought_content=agent_response.get_text_content(),
                agent=agent_name,
            )

        return agent_response

    def execute_routing(
        self,
        routing: RoutingInstruction,
        depth: int = 0,
        max_depth: int = 5,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        reset_depth_for_agents: bool = True,
        token_replacements: Optional[Dict[str, str]] = None,
    ) -> AgentResponse:
        """
        Execute a routing instruction with proper tracking.

        Args:
            routing: The routing instruction to execute
            depth: Current routing depth (for loop detection)
            max_depth: Maximum routing depth allowed
            conversation_history: Optional history to include
            reset_depth_for_agents: Whether to reset depth counter when routing to a new agent
            token_replacements: Optional dictionary of token replacements to use for this agent's system prompt

        Returns:
            The final response after routing execution
        """
        if depth >= max_depth:
            return self.execute_agent(
                agent_name=routing.source_agent.value,
                message=MessageContent.simple_tool_result(
                    tool_id=routing.tool_call.tool_id,
                    output="Maximum tool calls this conversation turn reached. Please provide the user a response.",
                    error=True,
                ),
                conversation_history=conversation_history,
                token_replacements=token_replacements,
            )

        # When routing between agents, we can optionally reset the depth counter
        next_depth = 0 if reset_depth_for_agents else depth + 1
        tool_response = []
        routing_result = None
        error_result = None

        if routing.is_agent_routing():
            # Route to another agent
            target_agent: str | None = routing.tool_call.tool_input.get("target_agent", None)
            message = routing.tool_call.tool_input.get("message", "No message content provided")

            # Format the message for the target agent
            routed_message = f"## Routed message from agent: {routing.source_agent}"
            routed_message += f"\n\n{message}"

            if target_agent is None or target_agent not in self.agents:
                # Build the ToolResponse object for the error to allow the agent to try something else
                tool_response.append(
                    ToolResponse(
                        tool_id=routing.tool_call.tool_id,
                        content=json.dumps(
                            {
                                "result": "This tool is unavailable",
                                "tool_name": routing.tool_call.tool_name,
                                "content": "You asked to route to an agent that doesn't exist. Confirm your available agents with the schema for this tool or try a different target agent.",
                            }
                        ),
                        is_error=True,
                    )
                )
            else:
                # Add event to queue for routing request
                if True:
                    self.console_adapter.display_agent_request(
                        source_agent=routing.source_agent.value,
                        target_agent=target_agent,
                        message=routing.tool_call.tool_input.get("message", "*unspecified*"),
                    )

                # Execute the target agent with token replacement
                target_response = self.execute_agent(
                    agent_name=target_agent,
                    message=routed_message,
                    conversation_history=conversation_history,
                    token_replacements=token_replacements,
                )

                # If target agent is using tools, process those
                if target_response.is_using_tools():
                    target_response_tools = []
                    for route in target_response.routing:
                        # Recursively call this function for tools from the target agent
                        target_response_tools = self.execute_routing(
                            routing=route,
                            depth=next_depth,
                            max_depth=max_depth,
                            conversation_history=conversation_history,
                            reset_depth_for_agents=reset_depth_for_agents,
                            token_replacements=token_replacements,
                        )
                        # Format result for source agent
                        routing_result = {
                            "result": "Routing completed successfully",
                            "content": target_response_tools.get_text_content(),
                            "target_agent": target_agent,
                        }

                        # Build the ToolResponse object
                        tool_response.append(
                            ToolResponse(
                                tool_id=routing.tool_call.tool_id,
                                content=json.dumps(routing_result),
                            )
                        )
                else:
                    # Add event for routing response
                    if True:
                        self.console_adapter.display_agent_response(
                            source_agent=routing.source_agent.value,
                            target_agent=target_agent,
                            message=target_response.get_text_content(),
                        )

                    # Format result for source agent
                    routing_result = {
                        "result": "Routing completed successfully",
                        "content": target_response.get_text_content(),
                        "target_agent": target_agent,
                    }

                    # Build the ToolResponse object
                    tool_response.append(
                        ToolResponse(
                            tool_id=routing.tool_call.tool_id, content=json.dumps(routing_result)
                        )
                    )
        else:
            # Add event to queue for tool call
            if True:
                self.console_adapter.display_tool_call(
                    source_agent=routing.source_agent.value,
                    tool_name=routing.tool_call.tool_name,
                    tool_input=routing.tool_call.tool_input,
                )

            tool_name = routing.tool_call.tool_name

            # Tool restriction controls
            try:
                if tool_name in self.tools and hasattr(self.tools.get(tool_name), "handler"):
                    # The tool exists in the registry
                    tool = self.tools.get(tool_name)

                    # Check if the agent is allowed to use this tool
                    if tool_name in self.agents[routing.source_agent.value].allowed_tools:
                        try:
                            # Prepare tool input - handle dict-like objects from Anthropic API
                            tool_input = routing.tool_call.tool_input

                            # Invoke the tool with proper error handling
                            routing_result = tool.handler(tool_input)

                            # Build the ToolResponse for the tool handler
                            tool_response.append(
                                ToolResponse(
                                    tool_id=routing.tool_call.tool_id,
                                    content=json.dumps(routing_result),
                                )
                            )
                        except Exception as tool_error:
                            # Handle any exceptions during tool input preparation or execution
                            error_result = {
                                "success": False,
                                "message": f"Error executing tool {tool_name}: {str(tool_error)}",
                                "error": str(tool_error),
                            }
                            tool_response.append(
                                ToolResponse(
                                    tool_id=routing.tool_call.tool_id,
                                    content=json.dumps(error_result),
                                    is_error=True,
                                )
                            )
                    else:
                        # The agent is not allowed access to the requested tool
                        routing_result = {
                            "result": "Permission denied",
                            "tool_name": routing.tool_call.tool_name,
                            "content": f"The agent {routing.source_agent.value} does not have permission to use the {tool_name} tool.",
                        }

                        # Build the ToolResponse for the error
                        tool_response.append(
                            ToolResponse(
                                tool_id=routing.tool_call.tool_id,
                                content=json.dumps(routing_result),
                                is_error=True,
                            )
                        )
                else:
                    # The tool doesn't exist or doesn't have a handler
                    routing_result = {
                        "result": "Tool unavailable",
                        "tool_name": routing.tool_call.tool_name,
                        "content": f"The tool {tool_name} is not available or could not be loaded.",
                    }

                    # Build the ToolResponse for the error
                    tool_response.append(
                        ToolResponse(
                            tool_id=routing.tool_call.tool_id,
                            content=json.dumps(routing_result),
                            is_error=True,
                        )
                    )
            except Exception as e:
                # Handle any exceptions that occur during tool execution
                error_msg = str(e)
                routing_result = {
                    "result": "Tool execution failed",
                    "tool_name": routing.tool_call.tool_name,
                    "content": f"Error executing tool {tool_name}: {error_msg}",
                }

                # Build the ToolResponse for the error
                tool_response.append(
                    ToolResponse(
                        tool_id=routing.tool_call.tool_id,
                        content=json.dumps(routing_result),
                        is_error=True,
                    )
                )

            # Add event to queue for tool response
            if True:
                self.console_adapter.display_tool_response(
                    target_agent=routing.source_agent.value,
                    tool_name=routing.tool_call.tool_name,
                    tool_output=(
                        routing_result
                        if routing_result is not None
                        else error_result
                        if error_result is not None
                        else "No output provided"
                    ),
                )

        # Format the tool result for the source agent
        for i, tool in enumerate(tool_response):
            tool_response[i] = MessageContent.make_tool_result(tool)

        # Execute the source agent with the tool result and token replacement
        final_response = self.execute_agent(
            agent_name=routing.source_agent.value,
            message=tool_response,
            conversation_history=conversation_history,
            token_replacements=token_replacements,
        )

        # If source agent is using more tools, process those
        if final_response.is_using_tools():
            for route in final_response.routing:
                final_response = self.execute_routing(
                    routing=route,
                    depth=next_depth,
                    conversation_history=conversation_history,
                    max_depth=max_depth,
                    reset_depth_for_agents=False,
                    token_replacements=token_replacements,
                )

        return final_response

    def _build_context_message(self, user_message: str, user_id: str) -> str:
        """
        Build a context message for the dispatcher agent.

        Args:
            user_message: The user's message

        Returns:
            Formatted context message
        """

        # Create the context message
        context_message = (
            f"<UserMessage>\n{user_message}\n</UserMessage>\n<UserID>\n{user_id}\n</UserID>\n"
        )
        context_message += f"<CurrentDateTime>\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n</CurrentDateTime>"

        return context_message

    def _prepare_output_content(self, user_message: str, dispatcher_response: AgentResponse) -> str:
        """
        Prepare content for the outputter agent.

        Args:
            user_message: The user's message
            dispatcher_response: Response from the dispatcher

        Returns:
            Formatted content for outputter
        """
        return f"""
        ## User Message
        {user_message}

        ## Luna's Reasoning
        {dispatcher_response.get_text_content()}

        Please format this as a natural response from Luna to the user, maintaining her personality.
        """

    def _get_working_memory(self, user_id: str, user_message: str) -> str:
        """
        Get working memory relevant to the current conversation turn.

        This method would retrieve memories from a memory database or service
        that are most relevant to the current conversation context.

        Args:
            user_id: The user's ID
            user_message: The user's message

        Returns:
            String containing the working memory content
        """
        # This is a placeholder implementation
        # In a full implementation, this would query a memory service or database
        # to retrieve memories based on relevance to the current conversation

        # For now, just return a simple message
        return "No specific memories have been retrieved at this time."

    def _process_heartbeat(self) -> str:
        """
        Process a heartbeat message.

        Heartbeat messages allow Luna to think autonomously without direct user input.
        These are periodic events where Luna can reflect, grow, and evolve.

        Returns:
            Response message (typically empty as heartbeats don't produce user-visible output)
        """

        # Create a context message for the heartbeat
        context_message = "[HEARTBEAT] Timestamp: " + datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Execute the dispatcher agent for the heartbeat
        dispatcher_response = self.execute_agent(
            agent_name="dispatcher",
            message=context_message,
        )

        # Process routing instructions if any
        if dispatcher_response.is_using_tools():
            for route in dispatcher_response.routing:
                dispatcher_response = self.execute_routing(
                    routing=route,
                    depth=0,
                    max_depth=6,
                )

        # Store the heartbeat thought in memory
        # This would typically involve a call to a memory service
        # For now, we'll just log it
        thought_content = dispatcher_response.get_text_content()
        self.console_adapter.console.print(f"[dim]Heartbeat thought: {thought_content}[/dim]")

        # Heartbeats don't produce user-visible output, so return empty string
        return ""

    def _generate_intuition(self, user_id: str, user_message: str) -> str:
        """
        Generate intuition for the current conversation turn using the subconscious agent.

        This method would execute the subconscious agent outside of the normal
        processing flow to generate intuitive leaps or connections for Luna.

        Args:
            user_id: The user's ID
            user_message: The user's message

        Returns:
            String containing the intuition content
        """
        # Check if the subconscious agent exists
        if "subconscious" not in self.agents:
            return "No intuitive insights available at this time."

        try:
            # Get user profile
            user_profile = self.user_service.get_user_profile(user_id)
            user_profile_str = str(user_profile.to_dict()) if user_profile else None

            # Get emotional state
            emotional_state = self.emotion_service.get_current_state()
            emotion_label = self.emotion_service.get_emotion_label()

            emotional_state_dict = None
            if emotional_state:
                emotional_state_dict = {
                    "pleasure": emotional_state.pleasure,
                    "arousal": emotional_state.arousal,
                    "dominance": emotional_state.dominance,
                    "descriptor": emotion_label,
                }

            # Create a context message for the subconscious
            context_message = f"""
            ## User Message
            {user_message}

            ## User Profile
            {user_profile_str if user_profile_str else "No user profile available."}

            ## Emotional State
            {emotional_state_dict if emotional_state_dict else "No emotional state available."}
            """

            # Execute the subconscious agent
            subconscious_response = self.agents["subconscious"].execute(
                message=context_message,
                external_history=None,  # Subconscious doesn't need conversation history
            )

            # Extract the intuition text from the response
            if subconscious_response and subconscious_response.has_text():
                return subconscious_response.get_text_content()
            else:
                return "No intuitive insights available at this time."

        except Exception as e:
            # If anything goes wrong, just return a default message
            return "No intuitive insights available at this time."

    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics for the hub.

        Returns:
            Dictionary of statistics
        """
        return self.execution_stats.copy()
