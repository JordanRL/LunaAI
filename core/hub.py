"""
Hub implementation for Luna.

This module defines the hub implementation for Luna's hub-based architecture,
where the dispatcher serves as the central coordinator for all agent communication.
"""
import json
from typing import Dict, List, Any, Optional

from rich.prompt import Prompt

from adapters.console_adapter import ConsoleAdapter
from config.settings import get_api_keys, get_app_config
from core.agent import Agent
from domain.models.agent import AgentResponse
from domain.models.conversation import MessageContent
from domain.models.routing import RoutingInstruction, ToolResponse
from domain.models.tool import ToolRegistry
from services.conversation_service import ConversationService
from services.emotion_service import EmotionService
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
            user_service: UserService,
    ):
        """
        Initialize the Luna hub system.
        
        Args:
        """
        self.execution_stats = {
            "total_tokens": 0,
            "total_time": 0,
            "requests": 0
        }

        self._load_tools()
        self._load_agents()

        # Adapters
        self.console_adapter = console_adapter

        # Services
        self.conversation_service = conversation_service
        self.emotion_service = emotion_service
        self.user_service = user_service

        self.app_config = get_app_config()

    def _load_agents(self) -> None:
        """
        Load all agent components from the system_prompts directory.
        
        For each directory in system_prompts, this method:
        1. Reads the agent.json, summary.md, and system.md files
        2. Creates an AgentConfig object for the agent
        3. Creates an Agent instance using the AgentConfig
        4. Stores the Agent in self.agents dictionary with name as key
        """
        import os
        import json
        from domain.models.agent import AgentConfig
        from domain.models.enums import AgentType
        from core.agent import Agent
        from adapters.anthropic_adapter import AnthropicAdapter
        
        # Get the API key from environment
        api_keys = get_api_keys()
        api_adapter = AnthropicAdapter(api_key=api_keys.anthropic_api_key)
        
        self.agents = {}
        system_prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompts")
        
        # Iterate through directories in system_prompts
        for agent_dir in os.listdir(system_prompts_dir):
            agent_path = os.path.join(system_prompts_dir, agent_dir)
            
            # Skip if not a directory
            if not os.path.isdir(agent_path):
                continue
                
            # Check for required files
            agent_json_path = os.path.join(agent_path, "agent.json")
            system_md_path = os.path.join(agent_path, "system.md")
            
            # Skip if required files don't exist
            if not os.path.exists(agent_json_path) or not os.path.exists(system_md_path):
                continue
                
            # Load agent.json
            with open(agent_json_path, 'r') as file:
                agent_config_data = json.load(file)
                
            # Load system.md
            with open(system_md_path, 'r') as file:
                system_prompt = file.read()
                
            # Create AgentConfig object
            agent_name = agent_config_data.get("name")
            
            # Get tools for this agent
            tool_names = agent_config_data.get("tools", [])
            tools = []
            
            # After loading tools in _load_tools, populate the tools list
            if hasattr(self, 'tools') and self.tools is not None:
                for tool_name in tool_names:
                    tool = self.tools.get(tool_name)
                    if tool:
                        tools.append(tool)
            
            # Create AgentConfig
            agent_config = AgentConfig(
                name=AgentType(agent_name),
                model=agent_config_data.get("model", "claude-3-7-sonnet-latest"),
                system_prompt=system_prompt,
                tools=tools,
                max_tokens=agent_config_data.get("max_tokens", 4000),
                temperature=agent_config_data.get("temperature", 0.7)
            )
            
            # Create Agent instance
            agent = Agent(
                config=agent_config,
                api_adapter=api_adapter
            )
            
            # Store in agents dictionary
            self.agents[agent_name] = agent


    def _load_tools(self) -> None:
        """
        Load all tools from the domain/tools directory.
        
        This method dynamically discovers and loads all tools defined in the 
        domain/tools folder without requiring a hardcoded list. It then stores 
        them in the self.tools property as an instance of the ToolRegistry class.
        """
        import importlib
        import inspect
        import pkgutil
        import domain.tools
        from domain.models.tool import Tool, ToolRegistry
        
        # Initialize the tool registry
        self.tools = ToolRegistry()
        
        # Get the package directory for domain.tools
        for _, module_name, is_pkg in pkgutil.iter_modules(domain.tools.__path__, domain.tools.__name__ + '.'):
            if not is_pkg:  # Only process modules, not sub-packages
                # Import the module
                module = importlib.import_module(module_name)
                
                # Find all Tool classes in the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class and is a subclass of Tool but not Tool itself
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Tool) and 
                        obj is not Tool):
                        
                        # Instantiate the tool
                        tool_instance = obj()
                        
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
        commands = self._handle_command(user_message)

        if not commands:
            raise SystemExit("Time to quit. Goodbye!")

        # Get conversation ID
        conversation_id = self.conversation_service.get_conversation_id_by_user_id(user_id)
        if not conversation_id:
            conversation = self.conversation_service.create_conversation(user_id)
            conversation_id = conversation.conversation_id

        # Store user message in conversation
        self.conversation_service.add_user_message(conversation_id, MessageContent.make_text(user_message))
        
        # Create context message for dispatcher
        context_message = self._build_context_message(user_message, user_id)
        
        # Execute dispatcher agent
        dispatcher_response = self.execute_agent(
            agent_name="dispatcher",
            message=context_message,
            conversation_history=self.conversation_service.get_conversation(conversation_id),
        )
        
        # Process routing instructions if any
        if dispatcher_response.is_using_tools():
            for route in dispatcher_response.routing:
                dispatcher_response = self.execute_routing(
                    routing=route,
                    depth=0,
                    max_depth=6
                )
        
        # Format final response with outputter
        formatted_content = self._prepare_output_content(user_message, dispatcher_response)
        
        outputter_response = self.execute_agent(
            agent_name="outputter",
            message=formatted_content
        )
        
        final_response = outputter_response.message.content[-1]
        
        # Store assistant message in conversation
        self.conversation_service.add_assistant_message(
            conversation_id,
            final_response
        )
        
        # Decay emotional state
        self.emotion_service.decay()
        
        # Update user interaction stats
        self.user_service.update_interaction_stats(user_id)
        
        return outputter_response.message.get_text()

    def user_prompt(self):
        return Prompt(prompt="[bold cyan]You>[/bold cyan] ", console=self.console_adapter.console)
    
    def execute_agent(
            self,
            agent_name: str,
            message: str|MessageContent|List[MessageContent],
            conversation_history: Optional[List[Dict[str, Any]]] = None,
            suppress_thinking: bool = False,
    ) -> AgentResponse:
        """
        Execute a specific agent with proper context management.
        
        Args:
            agent_name: Name of the agent to execute
            message: Input message for the agent
            conversation_history: Optional history to include
            suppress_thinking: Whether to suppress the thinking message for this agent
            
        Returns:
            The final AgentResponse after all tool processing
        """
        if agent_name not in self.agents:
            # Return error response if agent not found
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        agent_response = agent.execute(message, conversation_history)

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
            reset_depth_for_agents: bool = True
    ) -> AgentResponse:
        """
        Execute a routing instruction with proper tracking.
        
        Args:
            routing: The routing instruction to execute
            depth: Current routing depth (for loop detection)
            max_depth: Maximum routing depth allowed
            conversation_history: Optional history to include
            reset_depth_for_agents: Whether to reset depth counter when routing to a new agent
            
        Returns:
            The final response after routing execution
        """
        if depth >= max_depth:
            return self.execute_agent(
                agent_name=routing.source_agent.value,
                message=MessageContent.simple_tool_result(
                        tool_id=routing.tool_call.tool_id,
                        output="Maximum tool calls this conversation turn reached. Please provide the user a response.",
                        error=True
                ),
                conversation_history=conversation_history
            )
        
        # When routing between agents, we can optionally reset the depth counter
        next_depth = 0 if reset_depth_for_agents else depth + 1
        tool_response = []

        if routing.is_agent_routing():
            # Route to another agent
            target_agent: str|None = routing.tool_call.tool_input.get("target_agent", None)
            message = routing.tool_call.tool_input.get("message", "No message content provided")
            
            # Format the message for the target agent
            routed_message = f"## Routed message from agent: {routing.source_agent}"
            routed_message += f"\n\n{message}"

            if target_agent is None or target_agent not in self.agents:
                # Build the ToolResponse object for the error to allow the agent to try something else
                tool_response.append(ToolResponse(
                    tool_id=routing.tool_call.tool_id,
                    content=json.dumps({
                        "result": "This tool is unavailable",
                        "tool_name": routing.tool_call.tool_name,
                        "content": "You asked to route to an agent that doesn't exist. Confirm your available agents with the schema for this tool or try a different target agent."
                    }),
                    is_error=True
                ))
            else:
                # Add event to queue for routing request
                if True:
                    self.console_adapter.display_agent_request(
                        source_agent=routing.source_agent.value,
                        target_agent=target_agent,
                        message=routing.tool_call.tool_input.get("message", "*unspecified*")
                    )

                # Execute the target agent
                target_response = self.execute_agent(
                    agent_name=target_agent,
                    message=routed_message,
                    conversation_history=conversation_history
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
                            reset_depth_for_agents=reset_depth_for_agents
                        )
                        # Format result for source agent
                        routing_result = {
                            "result": "Routing completed successfully",
                            "content": target_response.get_text_content(),
                            "target_agent": target_agent
                        }

                        # Build the ToolResponse object
                        tool_response.append(ToolResponse(
                            tool_id=routing.tool_call.tool_id,
                            content=json.dumps(routing_result)
                        ))
                else:
                    # Add event for routing response
                    if True:
                        self.console_adapter.display_agent_response(
                            source_agent=routing.source_agent.value,
                            target_agent=target_agent,
                            message=target_response.get_text_content()
                        )

                    # Format result for source agent
                    routing_result = {
                        "result": "Routing completed successfully",
                        "content": target_response.get_text_content(),
                        "target_agent": target_agent
                    }

                    # Build the ToolResponse object
                    tool_response.append(ToolResponse(
                        tool_id=routing.tool_call.tool_id,
                        content=json.dumps(routing_result)
                    ))
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
            if tool_name in self.agents[routing.source_agent.value].tools:
                # The agent is allowed access to the requested tool so invoke it
                tool = self.tools.get(tool_name)
                routing_result = tool.handler(routing.tool_call.tool_input)

                # Build the ToolResponse for the tool handler
                tool_response.append(ToolResponse(
                    tool_id=routing.tool_call.tool_id,
                    content=json.dumps(routing_result)
                ))
            else:
                # The agent is not allowed access to the requested tool to build the error
                routing_result = {
                    "result": "This tool is unavailable",
                    "tool_name": routing.tool_call.tool_name,
                    "content": "The tool could not be executed. Please make sure the tool name is correct."
                }

                # Build the ToolResponse for the error
                tool_response.append(ToolResponse(
                    tool_id=routing.tool_call.tool_id,
                    content=json.dumps(routing_result),
                    is_error=True
                ))

            # Add event to queue for tool response
            if True:
                self.console_adapter.display_tool_response(
                    target_agent=routing.source_agent.value,
                    tool_name=routing.tool_call.tool_name,
                    tool_output=routing_result
                )

        # Format the tool result for the source agent
        for i, tool in enumerate(tool_response):
            tool_response[i] = MessageContent.make_tool_result(tool)
        
        # Execute the source agent with the tool result
        final_response = self.execute_agent(
            agent_name=routing.source_agent.value,
            message=tool_response,
            conversation_history=conversation_history
        )
        
        # If source agent is using more tools, process those
        if final_response.is_using_tools():
            for route in final_response.routing:
                final_response = self.execute_routing(
                    routing=route,
                    depth=next_depth,
                    conversation_history=conversation_history,
                    max_depth=max_depth,
                    reset_depth_for_agents=False
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
        # Format memories if available
        memories_formatted = ""
        
        # Create the context message
        context_message = f"""
        ## User Message
        {user_message}
        
        ## User ID
        {user_id}
        
        ## User Profile
        {self.user_service.get_user_profile(user_id).to_dict()}
        """
        
        # Add emotional state
        emotional_state = self.emotion_service.get_current_state()
        relative_state = self.emotion_service.get_relative_state()
        emotion_label = self.emotion_service.get_emotion_label()
        
        context_message += f"""
        ## Emotional State
        Current: {emotional_state.to_dict()}
        Relative to baseline: {relative_state}
        Emotion label: {emotion_label}
        """
        
        # Add memories if available
        if memories_formatted:
            context_message += f"\n\n{memories_formatted}"
        
        return context_message
    
    def _prepare_output_content(self, user_message: str, dispatcher_response: Any) -> str:
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
        {dispatcher_response.content}
        
        Please format this as a natural response from Luna to the user, maintaining her personality.
        """
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics for the hub.
        
        Returns:
            Dictionary of statistics
        """
        return self.execution_stats.copy()