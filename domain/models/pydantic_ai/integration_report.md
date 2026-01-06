# PydanticAI Integration Report

## Executive Summary

This report provides an analysis of integrating PydanticAI into Luna's architecture to enable vendor-agnostic AI interactions, structured outputs, and advanced features. The integration would significantly reduce code complexity, enable cross-provider compatibility, and add new capabilities with minimal refactoring of business logic.

Key benefits include:
- **Provider Agnosticism**: Seamlessly use models from Anthropic, OpenAI, Gemini, and others
- **Type Safety**: Leverage Pydantic's validation for robust data handling
- **Reduced Boilerplate**: Eliminate vendor-specific message handling code
- **Advanced Features**: Access to thinking mode, structured outputs, and streaming

## Current Architecture Analysis

### Strengths
- **Domain-Driven Design**: Clear separation of business logic from infrastructure
- **Multi-Agent Framework**: Specialized agents for different cognitive functions
- **Comprehensive Memory System**: Sophisticated memory architecture
- **Rich Emotional System**: Complex emotional simulation

### Limitations
- **Vendor Lock-in**: Heavily reliant on Anthropic-specific formats
- **Manual Type Handling**: Limited automated validation
- **Redundant Adapters**: Multiple adapters for different providers
- **Complex Message Conversion**: Custom conversion between formats
- **Limited Metrics**: Basic token counting without detailed insights

## PydanticAI Architecture

PydanticAI provides a comprehensive framework for building AI applications:

### Core Components
- **Agent**: Central class for managing LLM interactions
- **Tools**: Function-based tool system with automatic schema generation
- **Messages**: Standardized message formats for cross-provider compatibility
- **Models**: Abstract representation of LLM providers and settings
- **Result Types**: Structured outputs with validation

### Key Features
- **Provider Abstraction**: Single interface for multiple providers
- **Type Safety**: Strong typing and validation throughout
- **Function Tools**: Tools defined as Python functions with automatic schema generation
- **Structured Outputs**: Define output schemas using Pydantic models
- **Message History**: Standardized conversation tracking
- **Metrics and Usage Tracking**: Detailed token and request metrics

## Integration Strategy

### Approach
We recommend a phased approach that allows incremental adoption:

1. **Agent-by-Agent Migration**: Convert individual agents while maintaining compatibility
2. **Parallel Implementations**: Maintain legacy and PydanticAI versions during transition
3. **Tool Conversion**: Convert tools incrementally, starting with simple functions
4. **Service Adaptation**: Update services to work with both implementations

This approach enables ongoing development while gradually migrating to PydanticAI.

### Technical Components

#### 1. Adapter Layer
Create adapters that convert between Luna's domain models and PydanticAI's models:
```python
class PAIAdapter:
    """Adapter for converting between domain models and PydanticAI models."""

    @staticmethod
    def convert_message_to_pai(message: LegacyMessage) -> ModelMessage:
        # Implementation...

    @staticmethod
    def convert_pai_message_to_legacy(message: ModelMessage) -> LegacyMessage:
        # Implementation...
```

#### 2. Agent Factory
Create a factory for PydanticAI agents that handles configuration and tool registration:
```python
class LunaPAIAgentFactory:
    """Factory for creating PydanticAI agents for Luna."""

    @staticmethod
    def create_agent(config: LunaAgentConfig, tools=None):
        agent = Agent(
            config.model_config.to_known_model_name(),
            name=config.name,
            system_prompt=config.system_prompt,
            # Additional configuration...
        )

        # Register tools if provided
        if tools:
            for tool in tools:
                agent.registry.register_tool(tool)

        return agent
```

#### 3. Tool Registration
Convert Luna's tool definitions to PydanticAI function tools:
```python
@memory_agent.tool
def search_memory(ctx: RunContext[Any], query: str, limit: int = 5) -> List[Dict]:
    """
    Search Luna's memory for information matching the query.

    Args:
        query: The search query string
        limit: Maximum number of results to return
    """
    # Implementation using existing memory_service
    return memory_service.search(query, limit)
```

#### 4. Message Handling
Update message handling to work with PydanticAI's message models:
```python
def process_response(agent_response):
    """Process a PydanticAI agent response."""
    # Extract text content
    text_content = ""
    for part in agent_response.messages[-1].parts:
        if hasattr(part, "content") and isinstance(part.content, str):
            text_content += part.content

    # Process tool calls
    tool_calls = []
    for part in agent_response.messages[-1].parts:
        if hasattr(part, "part_kind") and part.part_kind == "tool-call":
            tool_calls.append({
                "name": part.tool_name,
                "id": part.tool_call_id,
                "arguments": part.args_as_dict()
            })

    return text_content, tool_calls
```

#### 5. System Prompt Management
Convert Luna's token replacement mechanism to PydanticAI's system prompt functions:
```python
@agent.system_prompt
def dynamic_system_prompt(ctx: RunContext[Any]) -> str:
    """Generate dynamic system prompt with token replacements."""
    base_prompt = load_base_prompt("dispatcher")

    # Apply replacements
    persona_config = ctx.deps.get("persona_config", {})
    emotional_state = ctx.deps.get("emotional_state", {})

    replaced_prompt = base_prompt.replace(
        "{{PERSONA_NAME}}", persona_config.get("name", "Luna")
    ).replace(
        "{{EMOTIONAL_STATE}}", emotional_state.get("description", "neutral")
    )

    return replaced_prompt
```

## Implementation Roadmap

### Phase 1: Foundations (2-3 weeks)
- Create adapter infrastructure
- Implement agent factory
- Set up configuration system
- Create integration tests

### Phase 2: Agent Migration (4-6 weeks)
- Convert one agent type completely (e.g., Memory Retriever)
- Test in isolation
- Document patterns and challenges
- Convert remaining agents

### Phase 3: Hub Refactoring (2-3 weeks)
- Update hub architecture
- Implement cross-agent communication
- Enable structured data exchange
- Test end-to-end functionality

### Phase 4: Feature Enhancements (2-4 weeks)
- Implement advanced features (streaming, thinking mode)
- Enable cross-provider compatibility
- Add metrics and monitoring
- Optimize performance

## Risk Assessment

### Potential Challenges
1. **System Prompt Conversion**: Luna's XML-based prompts may require restructuring
2. **Tool Schema Compatibility**: Ensuring consistent tool behavior across implementations
3. **Message Format Conversion**: Managing differences in content structures
4. **Testing Coverage**: Ensuring comprehensive testing during transition

### Mitigation Strategies
1. Create robust test cases for each agent before migration
2. Implement thorough validation during adapter conversion
3. Maintain parallel implementations for critical components
4. Document patterns and anti-patterns for PydanticAI integration

## Conclusion

Integrating PydanticAI into Luna's architecture offers significant advantages in terms of code simplification, provider agnosticism, and access to advanced features. By following a phased approach, we can minimize disruption while progressively enhancing functionality.

The proposed integration strategy enables:
- Incremental adoption with minimal risk
- Ongoing development during migration
- Preservation of domain-specific business logic
- Significant reduction in boilerplate code

We recommend proceeding with Phase 1 (Foundations) to establish the core infrastructure, then evaluating progress before proceeding to subsequent phases.

## Appendix

### A. Sample Code Repository

The `/domain/models/pydantic_ai/` directory contains reference implementations:
- `adapter.py`: Conversion between domain and PydanticAI models
- `config.py`: Configuration models for PydanticAI integration
- `example.py`: Example agent implementation
- `implementation_guide.md`: Detailed implementation guidelines
- `refactoring_plan.md`: Step-by-step refactoring plan

### B. Key Dependencies

- **pydantic-ai**: Core framework for agent interactions
- **pydantic**: Data validation and settings management
- **httpx**: HTTP client for API calls
- **logfire** (optional): Enhanced logging and monitoring
