"""
Domain-specific tool implementations.
"""

# Import tool classes
from domain.tools.routing import RouteToAgentTool, ContinueThinkingTool
from domain.tools.memory import MemoryRetrieverTool, MemoryWriterTool
from domain.tools.cognition import InnerThoughtTool, ReflectionTool
from domain.tools.emotion import EmotionAdjustmentTool
from domain.tools.relationship import RelationshipUpdateTool

# Import the registry
from domain.models.tool import ToolRegistry, ToolCategory

# Initialize registry
TOOL_REGISTRY = ToolRegistry()

def register_all_tools() -> ToolRegistry:
    """Register all available tools in the global registry."""
    # Initialize all tool instances
    route_to_agent_tool = RouteToAgentTool()
    continue_thinking_tool = ContinueThinkingTool()
    memory_retriever_tool = MemoryRetrieverTool()
    memory_writer_tool = MemoryWriterTool()
    inner_thought_tool = InnerThoughtTool()
    reflection_tool = ReflectionTool()
    emotion_adjustment_tool = EmotionAdjustmentTool()
    relationship_update_tool = RelationshipUpdateTool()
    
    # Register routing tools
    TOOL_REGISTRY.register(route_to_agent_tool)
    TOOL_REGISTRY.register(continue_thinking_tool)
    
    # Register memory tools
    TOOL_REGISTRY.register(memory_retriever_tool)
    TOOL_REGISTRY.register(memory_writer_tool)
    
    # Register cognition tools
    TOOL_REGISTRY.register(inner_thought_tool)
    TOOL_REGISTRY.register(reflection_tool)
    
    # Register emotion tool
    TOOL_REGISTRY.register(emotion_adjustment_tool)
    
    # Register relationship tool
    TOOL_REGISTRY.register(relationship_update_tool)
    
    return TOOL_REGISTRY

# Expose all tool classes
__all__ = [
    'RouteToAgentTool',
    'ContinueThinkingTool',
    'MemoryRetrieverTool',
    'MemoryWriterTool',
    'InnerThoughtTool',
    'ReflectionTool',
    'EmotionAdjustmentTool',
    'RelationshipUpdateTool',
    'TOOL_REGISTRY',
    'register_all_tools'
]