from enum import Enum
from inspect import Parameter, signature
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field, create_model

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


class Tool(BaseModel, Generic[ToolInputType, ToolResultType]):
    """
    Represents a tool that can be used by an agent.

    This model defines a tool that can be registered with a PydanticAI agent
    and provides utility methods for working with tools.

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
    handler: Callable[[ToolInputType], ToolResultType]
    category: Optional[ToolCategory] = None

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[ToolCategory] = None,
    ) -> "Tool":
        """
        Create a Tool from a Python function.

        This method inspects the function signature and docstring to generate
        a tool definition that can be used with PydanticAI.

        Args:
            func: The function to convert to a tool
            name: Optional name override (default: function name)
            description: Optional description override (default: function docstring)
            category: Optional tool category

        Returns:
            A Tool instance ready for registration with a PydanticAI agent
        """
        func_name = name or func.__name__
        func_doc = description or (func.__doc__ or "").strip()

        # Get function signature to extract parameter information
        sig = signature(func)
        parameters = {}

        for param_name, param in sig.parameters.items():
            if param.name == "self" or param.name == "cls":
                continue

            param_type = param.annotation if param.annotation != Parameter.empty else Any
            param_default = None if param.default == Parameter.empty else param.default

            parameters[param_name] = (
                param_type,
                ... if param_default == Parameter.empty else param_default,
            )

        # Create a Pydantic model for the input schema
        InputModel = create_model(f"{func_name.title()}Input", **parameters)

        # Extract JSON schema
        input_schema = {
            "type": "object",
            "properties": InputModel.model_json_schema()["properties"],
            "required": InputModel.model_json_schema().get("required", []),
        }

        # Create and return the Tool
        return cls(
            name=func_name,
            description=func_doc,
            input_schema=input_schema,
            handler=func,
            category=category,
        )

    def to_api_schema(self) -> Dict[str, Any]:
        """Convert to Anthropic API schema format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI API schema format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def safe_execute(self, input_data: Any) -> Dict[str, Any]:
        """
        Safely execute the tool handler with input type conversion.

        This method provides error handling and standardized responses
        for tool execution.

        Args:
            input_data: The input data from the tool call, which may be a dict,
                      an API object, or another type that needs conversion

        Returns:
            Dict[str, Any]: The result of the tool execution or an error object
        """
        try:
            # Convert to Dict if it's not already (handle both dict and API input object)
            if not isinstance(input_data, dict):
                # Try to convert to dict based on the object type
                if hasattr(input_data, "__dict__"):
                    input_data = input_data.__dict__
                elif hasattr(input_data, "model_dump"):
                    input_data = input_data.model_dump()
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


class ToolRegistry(BaseModel):
    """
    Registry for managing the available tools.

    This model provides a way to register and manage tools for
    different agents and categories.

    Attributes:
        tools: Dictionary mapping tool names to Tool objects
        agent_tools: Dictionary mapping agent types to lists of tool names
        tools_by_category: Dictionary mapping tool categories to lists of tool names
    """

    tools: Dict[str, Tool] = Field(default_factory=dict)
    agent_tools: Dict[str, List[str]] = Field(default_factory=dict)
    tools_by_category: Dict[ToolCategory, List[str]] = Field(
        default_factory=lambda: {cat: [] for cat in ToolCategory}
    )

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry"""
        self.tools[tool.name] = tool

        # Register the tool in its category
        if tool.category:
            if tool.name not in self.tools_by_category[tool.category]:
                self.tools_by_category[tool.category].append(tool.name)

    def register_agent_tool(self, tool_name: str, agent_type: str) -> List[str]:
        """Register a tool for an agent type"""
        if agent_type not in self.agent_tools:
            self.agent_tools[agent_type] = []

        if tool_name not in self.agent_tools[agent_type]:
            self.agent_tools[agent_type].append(tool_name)

        return self.agent_tools[agent_type]

    def register_agent_tools(self, tools: List[str], agent_type: str) -> List[str]:
        """Register multiple tools for an agent type"""
        for tool in tools:
            self.register_agent_tool(tool, agent_type)

        return self.agent_tools[agent_type]

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def get_all(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self.tools.values())

    def get_all_api_schemas(self, provider: str = "anthropic") -> List[Dict[str, Any]]:
        """
        Get all tools in API schema format for a specific provider

        Args:
            provider: The provider to get schemas for (anthropic, openai, etc.)

        Returns:
            List of tool schemas formatted for the requested provider
        """
        if provider == "openai":
            return [tool.to_openai_schema() for tool in self.tools.values()]
        # Default to Anthropic format
        return [tool.to_api_schema() for tool in self.tools.values()]

    def get_tools_for_agent(self, agent_type: str) -> List[str]:
        """Get list of tool names for an agent type"""
        return self.agent_tools.get(agent_type, [])

    def get_agent_api_schemas(
        self, agent_type: str, provider: str = "anthropic"
    ) -> List[Dict[str, Any]]:
        """Get API schemas for an agent's tools"""
        tool_names = self.get_tools_for_agent(agent_type)
        if provider == "openai":
            return [
                self.tools[name].to_openai_schema() for name in tool_names if name in self.tools
            ]
        # Default to Anthropic format
        return [self.tools[name].to_api_schema() for name in tool_names if name in self.tools]

    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in a specific category"""
        tool_names = self.tools_by_category.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]

    def get_category_api_schemas(
        self, category: ToolCategory, provider: str = "anthropic"
    ) -> List[Dict[str, Any]]:
        """Get API schemas for all tools in a category"""
        tool_names = self.tools_by_category.get(category, [])
        if provider == "openai":
            return [
                self.tools[name].to_openai_schema() for name in tool_names if name in self.tools
            ]
        # Default to Anthropic format
        return [self.tools[name].to_api_schema() for name in tool_names if name in self.tools]

    def register_tools_for_category(self, agent_type: str, category: ToolCategory) -> None:
        """Register all tools of a specific category for an agent type"""
        tool_names = self.tools_by_category.get(category, [])
        for tool_name in tool_names:
            self.register_agent_tool(tool_name, agent_type)

    def get_categories(self) -> Dict[ToolCategory, int]:
        """Get all categories and the number of tools in each"""
        return {cat: len(tools) for cat, tools in self.tools_by_category.items() if tools}

    def to_pydantic_ai_tools(self) -> List[Callable]:
        """
        Convert all tools to PydanticAI-compatible function tools.

        Returns:
            List of function tools that can be used with PydanticAI agents
        """
        return [tool.handler for tool in self.tools.values()]

    def __contains__(self, tool_name: str) -> bool:
        """
        Support for the 'in' operator to check if a tool exists.

        Args:
            tool_name: The name of the tool to check

        Returns:
            bool: True if the tool exists in the registry, False otherwise
        """
        return tool_name in self.tools
