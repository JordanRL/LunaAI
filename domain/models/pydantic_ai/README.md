# PydanticAI Integration Architecture

This directory contains the necessary components to integrate PydanticAI into our existing architecture.

## Key Components

### 1. Agent Management

Instead of our custom `Agent` class, we'll directly use PydanticAI's `Agent` class:

```python
from pydantic_ai import Agent

agent = Agent(
    "anthropic:claude-sonnet-4-5",  # Model to use
    system_prompt="You are Luna, a helpful assistant...",
    result_type=str,  # Default result type is string
    tools=[tool1, tool2],  # Tool functions
)

# Run the agent
result = agent.run_sync("Hello, how are you?")
```

### 2. Tool Integration

We'll convert our domain tools to PydanticAI function tools:

```python
@agent.tool
def retrieve_memory(ctx: RunContext, query: str, limit: int = 5) -> List[Dict]:
    """
    Retrieve memories relevant to the query.

    Args:
        query: The search query
        limit: Maximum number of memories to return

    Returns:
        List of memory objects
    """
    # Implementation using our memory service
    return memory_service.search(query, limit)
```

### 3. Message Handling

We'll use PydanticAI's built-in message models:

```python
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart

# Create a text response
text_response = ModelResponse(
    parts=[TextPart(content="Hello, how can I help you?")],
    model_name="claude-sonnet-4-5"
)

# Create a tool call
tool_call = ToolCallPart(
    tool_name="retrieve_memory",
    args={"query": "user hobbies", "limit": 3},
    tool_call_id="abc123"
)
```

### 4. Adapter Layer

We'll create adapters that convert between our domain models and PydanticAI models:

```python
class PAIAdapter:
    """Adapts PydanticAI components to our domain models."""

    @staticmethod
    def convert_message_to_pai(message: domain.Message) -> pydantic_ai.messages.ModelMessage:
        """Convert our domain message to PydanticAI message."""
        # Implementation...

    @staticmethod
    def convert_message_from_pai(message: pydantic_ai.messages.ModelMessage) -> domain.Message:
        """Convert PydanticAI message to our domain message."""
        # Implementation...
```

### 5. Hub Architecture

Our `LunaHub` will be refactored to use PydanticAI's multi-agent capabilities:

```python
class LunaHub:
    """Central hub using PydanticAI for agent orchestration."""

    def __init__(self, user_id: str, ...):
        # Initialize services
        self.agents = self._create_agents()

    def _create_agents(self) -> Dict[str, pydantic_ai.Agent]:
        """Create all the specialized agents."""
        agents = {}

        # Create dispatcher agent
        dispatcher = Agent(
            "anthropic:claude-sonnet-4-5",
            system_prompt=self._load_system_prompt("dispatcher"),
            tools=[self._route_to_agent],
            name="dispatcher"
        )
        agents["dispatcher"] = dispatcher

        # Create other agents...

        return agents

    @staticmethod
    def _route_to_agent(ctx: RunContext, target_agent: str, message: str) -> str:
        """Tool for routing between agents."""
        # Implementation for agent routing
```

## Migration Path

1. Create adapters for converting between our domain models and PydanticAI models
2. Refactor one agent at a time to use PydanticAI directly
3. Update the hub to orchestrate PydanticAI agents
4. Gradually convert tools to use PydanticAI's function tool pattern
5. Update services to work with both legacy and PydanticAI components
