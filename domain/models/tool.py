import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

# Type variables for generic tool input/output
ToolInputType = TypeVar("ToolInputType")
ToolResultType = TypeVar("ToolResultType")


class ToolCategory(Enum):
    """
    Categories of tools for organization.
    """

    ROUTING = "routing"
    MEMORY = "memory"
    EMOTION = "emotion"
    RELATIONSHIP = "relationship"
    COGNITION = "cognition"
    SYSTEM = "system"


class ToolScope(Enum):
    """
    Scope for the tool instances
    """

    GLOBAL = "global"
    PER_AGENT = "per_agent"
    CONFIG_PER_AGENT = "config_per_agent"


@dataclass
class Tool(Generic[ToolInputType, ToolResultType]):
    """
    Represents a tool that can be used by an agent.

    Attributes:
        name: The name of the tool
        description: Detailed description of what the tool does
        input_schema: JSON schema for the input parameters
        handler: Function that processes the tool input
        category: The category this tool belongs to
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[
        [Any], ToolResultType
    ]  # Using Any to support both dict and Anthropic object inputs
    category: Optional[ToolCategory] = None
    scope: ToolScope = ToolScope.GLOBAL
    instance_config: Optional[Dict[str, Any]] = None
    config_handler: Optional[Callable[[], bool]] = None

    def update_tool_def(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if input_schema is not None:
            self.input_schema = input_schema

    def update_config(self, config: Dict[str, Any]):
        self.instance_config = config
        if self.config_handler is not None:
            self.config_handler()
        return True

    def to_api_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic API schema format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def safe_execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Safely execute the tool handler with input type conversion.

        This method provides a standard way to handle tool inputs, converting
        Anthropic API objects to dictionaries when needed, and catching any
        exceptions that occur during execution.

        Args:
            input_data: The input data from the tool call, which may be a dict,
                       an Anthropic API object, or another type that needs conversion

        Returns:
            Dict[str, Any]: The result of the tool execution or an error object
        """
        try:
            # Convert to Dict if it's not already (handle both dict and Anthropic input object)
            if not isinstance(input_data, dict):
                # Try to convert to dict based on the object type
                if hasattr(input_data, "__dict__"):
                    input_data = input_data.__dict__
                elif hasattr(input_data, "items"):
                    # If it has items() method, assume it's dict-like
                    input_data = {k: v for k, v in input_data.items()}
                elif hasattr(input_data, "keys"):
                    # Another dict-like approach
                    input_data = {k: input_data[k] for k in input_data.keys()}

            # Call the handler with the prepared input
            return self.handler(input_data)

        except Exception as e:
            # Return a standardized error response
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing {self.name}: {str(e)}",
            }


@dataclass
class ToolRegistry:
    """
    Registry for managing the available tools.

    Attributes:
        tools: Dictionary mapping tool names to Tool objects
        agent_tools: Dictionary mapping agent types to lists of tool names
        tools_by_category: Dictionary mapping tool categories to lists of tool names
    """

    tools: Dict[str, Tool] = field(default_factory=dict)
    agent_tools: Dict[str, List[str]] = field(default_factory=dict)
    agent_instances: Dict[str, Dict[str, Tool]] = field(default_factory=dict)
    tools_by_category: Dict[ToolCategory, List[str]] = field(
        default_factory=lambda: {cat: [] for cat in ToolCategory}
    )

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry"""
        self.tools[tool.name] = tool

        # Register the tool in its category
        if tool.category:
            if tool.name not in self.tools_by_category[tool.category]:
                self.tools_by_category[tool.category].append(tool.name)

    def register_agent_tool(
        self,
        tool_name: str,
        agent_type: str,
        tool_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[str]:
        """Register a tool for an agent type"""
        if agent_type not in self.agent_tools:
            self.agent_tools[agent_type] = []

        if agent_type not in self.agent_instances:
            self.agent_instances[agent_type] = {}

        if tool_name not in self.agent_tools[agent_type]:
            self.agent_tools[agent_type].append(tool_name)

        if (
            tool_name in self.tools
            and tool_name not in self.agent_instances[agent_type]
            and isinstance(self.tools[tool_name], Tool)
            and self.tools[tool_name].scope is not ToolScope.GLOBAL
        ):
            self.agent_instances[agent_type][tool_name] = copy.deepcopy(self.tools[tool_name])

            if (
                self.tools[tool_name].scope == ToolScope.CONFIG_PER_AGENT
                and tool_config is not None
            ):
                self.agent_instances[agent_type][tool_name].update_config(tool_config)

        return self.agent_tools[agent_type]

    def register_agent_tools(
        self, tools: List[str], agent_type: str, tool_configs: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Register multiple tools for an agent type"""
        if agent_type not in self.agent_tools:
            self.agent_tools[agent_type] = []

        for tool in tools:
            if tool_configs is not None and tool in tool_configs:
                self.register_agent_tool(tool, agent_type, tool_configs[tool])
            else:
                self.register_agent_tool(tool, agent_type)

        return self.agent_tools[agent_type]

    def get(self, name: str, agent: Optional[str] = None) -> Optional[Tool]:
        """Get a tool by name"""
        if agent is not None and name in self.agent_instances[agent]:
            return self.agent_instances[agent][name]
        return self.tools.get(name)

    def get_all(self, agent: Optional[str] = None) -> List[Tool]:
        """Get all registered tools"""
        if agent is not None:
            tool_list = []
            for tool in self.agent_tools[agent]:
                this_tool = self.get(tool, agent)
                if this_tool is not None:
                    tool_list.append(this_tool)
        else:
            tool_list = list(self.tools.values())
        return tool_list

    def get_available(self, agent: Optional[str] = None) -> List[str]:
        if agent is not None:
            tool_list = self.agent_tools[agent]
        else:
            tool_list = list(self.tools.keys())
        return tool_list

    def get_all_api_schemas(self) -> List[Dict[str, Any]]:
        """Get all tools in API schema format"""
        return [tool.to_api_schema() for tool in self.tools.values()]

    def get_tools_for_agent(self, agent_type: str) -> List[str]:
        """Get list of tool names for an agent type"""
        return self.agent_tools.get(agent_type, [])

    def get_agent_api_schemas(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get API schemas for an agent's tools"""
        tool_names = self.get_tools_for_agent(agent_type)
        return [self.tools[name].to_api_schema() for name in tool_names if name in self.tools]

    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in a specific category"""
        tool_names = self.tools_by_category.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]

    def get_category_api_schemas(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Get API schemas for all tools in a category"""
        tool_names = self.tools_by_category.get(category, [])
        return [self.tools[name].to_api_schema() for name in tool_names if name in self.tools]

    def register_tools_for_category(self, agent_type: str, category: ToolCategory) -> None:
        """Register all tools of a specific category for an agent type"""
        tool_names = self.tools_by_category.get(category, [])
        for tool_name in tool_names:
            self.register_agent_tool(tool_name, agent_type)

    def get_categories(self) -> Dict[ToolCategory, int]:
        """Get all categories and the number of tools in each"""
        return {cat: len(tools) for cat, tools in self.tools_by_category.items() if tools}

    def __contains__(self, tool_name: str) -> bool:
        """
        Support for the 'in' operator to check if a tool exists.

        Args:
            tool_name: The name of the tool to check

        Returns:
            bool: True if the tool exists in the registry, False otherwise
        """
        return tool_name in self.tools
