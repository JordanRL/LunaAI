"""
Domain-specific tool implementations.
"""

# Import tool classes
from domain.tools.routing import RouteToAgentTool, ContinueThinkingTool
from domain.tools.memory import MemoryReadTool
from domain.tools.episodic_memory import EpisodicMemoryReadTool, EpisodicMemoryWriteTool
from domain.tools.semantic_memory import SemanticMemoryReadTool, SemanticMemoryWriteTool
from domain.tools.emotional_memory import EmotionalMemoryReadTool, EmotionalMemoryWriteTool
from domain.tools.relationship_memory import RelationshipMemoryReadTool, RelationshipMemoryWriteTool
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
    memory_read_tool = MemoryReadTool()
    
    # Initialize memory tools
    episodic_memory_read_tool = EpisodicMemoryReadTool()
    episodic_memory_write_tool = EpisodicMemoryWriteTool()
    semantic_memory_read_tool = SemanticMemoryReadTool()
    semantic_memory_write_tool = SemanticMemoryWriteTool()
    emotional_memory_read_tool = EmotionalMemoryReadTool()
    emotional_memory_write_tool = EmotionalMemoryWriteTool()
    relationship_memory_read_tool = RelationshipMemoryReadTool()
    relationship_memory_write_tool = RelationshipMemoryWriteTool()
    
    # Initialize other tools
    inner_thought_tool = InnerThoughtTool()
    reflection_tool = ReflectionTool()
    emotion_adjustment_tool = EmotionAdjustmentTool()
    relationship_update_tool = RelationshipUpdateTool()
    
    # Register routing tools
    TOOL_REGISTRY.register(route_to_agent_tool)
    TOOL_REGISTRY.register(continue_thinking_tool)
    
    # Register memory tools
    TOOL_REGISTRY.register(memory_read_tool)
    TOOL_REGISTRY.register(episodic_memory_read_tool)
    TOOL_REGISTRY.register(episodic_memory_write_tool)
    TOOL_REGISTRY.register(semantic_memory_read_tool)
    TOOL_REGISTRY.register(semantic_memory_write_tool)
    TOOL_REGISTRY.register(emotional_memory_read_tool)
    TOOL_REGISTRY.register(emotional_memory_write_tool)
    TOOL_REGISTRY.register(relationship_memory_read_tool)
    TOOL_REGISTRY.register(relationship_memory_write_tool)
    
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
    'MemoryReadTool',
    'EpisodicMemoryReadTool',
    'EpisodicMemoryWriteTool',
    'SemanticMemoryReadTool',
    'SemanticMemoryWriteTool',
    'EmotionalMemoryReadTool',
    'EmotionalMemoryWriteTool',
    'RelationshipMemoryReadTool',
    'RelationshipMemoryWriteTool',
    'InnerThoughtTool',
    'ReflectionTool',
    'EmotionAdjustmentTool',
    'RelationshipUpdateTool',
    'TOOL_REGISTRY',
    'register_all_tools'
]