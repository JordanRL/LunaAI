# PydanticAI Agent Implementation Guide

This guide provides practical instructions for implementing Luna agents using PydanticAI, focusing on real-world examples and best practices.

## Basic Agent Implementation

### 1. Creating an Agent

```python
from pydantic_ai import Agent
from pydantic_ai.tools import RunContext
from typing import Dict, List, Any

# Create a basic agent
memory_retriever = Agent(
    "anthropic:claude-sonnet-4-5",
    name="memory_retriever",
    system_prompt="""
    You are Luna's Memory Retriever agent.
    Your role is to search Luna's memory for relevant information based on the user's query.

    Wait for input and then search for related memories to provide context.
    """
)
```

### 2. Adding Tools to an Agent

```python
# Add a tool to the agent using the decorator pattern
@memory_retriever.tool
def search_episodic_memory(ctx: RunContext[Any], query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Luna's episodic memory for relevant information.

    Args:
        query: The search query string
        limit: Maximum number of results to return

    Returns:
        List of memory objects matching the query
    """
    # Implementation using memory_service
    memories = memory_service.search_episodic(query, limit)
    return [memory.to_dict() for memory in memories]
```

### 3. Using Structured Outputs

```python
from pydantic import BaseModel, Field

# Define a structured output model
class MemorySearchResult(BaseModel):
    """Results from a memory search operation."""

    memories: List[Dict[str, Any]] = Field(description="List of retrieved memories")
    context: str = Field(description="Contextual explanation of these memories")
    relation_to_query: str = Field(description="How these memories relate to the query")

# Create an agent with structured output
memory_analyser = Agent(
    "anthropic:claude-sonnet-4-5",
    name="memory_analyser",
    result_type=MemorySearchResult,  # Specify the result type
    system_prompt="You analyze memories to provide context about the user."
)
```

## Converting Luna's Components

### 1. Converting System Prompts

Luna currently uses XML-based system prompts with token replacement. Here's how to convert them:

```python
# Original Luna system prompt loading
def load_system_prompt(agent_name):
    with open(f"system_prompts/{agent_name}/system.json") as f:
        return json.load(f)["system_prompt"]

# PydanticAI implementation
@dispatcher_agent.system_prompt
def dynamic_system_prompt(ctx: RunContext[Any]) -> str:
    """Generate the system prompt for the dispatcher agent."""
    # Load the base prompt
    base_prompt = load_system_prompt("dispatcher")

    # Add dynamic elements
    return base_prompt.format(
        timestamp=ctx.timestamp.isoformat(),
        persona="Luna",
        # Add other replacements
    )
```

### 2. Converting Tools

Tools in Luna use a schema-based approach. Here's how to convert them:

```python
# Original Luna tool
class MemorySearchTool(Tool):
    def __init__(self, memory_service):
        super().__init__(
            name="search_memory",
            description="Search Luna's memory for relevant information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["query"]
            },
            handler=self.handle_search
        )
        self.memory_service = memory_service

    def handle_search(self, params):
        query = params.get("query")
        limit = params.get("limit", 5)
        return self.memory_service.search(query, limit)

# PydanticAI version
@agent.tool
def search_memory(ctx: RunContext[Any], query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Luna's memory for relevant information.

    Args:
        query: Search query
        limit: Max results

    Returns:
        List of memory objects
    """
    return memory_service.search(query, limit)
```

### 3. Converting Agent Execution

```python
# Original Luna execution
def execute_agent(agent_name, message, history):
    agent = agents[agent_name]
    response = agent.execute(message, history)
    return response

# PydanticAI execution
def execute_agent(agent_name: str, message: str, history=None):
    agent = pai_agents[agent_name]
    message_history = []

    if history:
        # Convert history to PydanticAI format
        message_history = PAIAdapter.convert_conversation_to_pai_history(history)

    # Execute the agent
    result = agent.run_sync(message, message_history=message_history)
    return result
```

## Hub Integration

### 1. Multi-Agent Orchestration

```python
from pydantic_ai.messages import ModelRequest, ModelResponse

# Example dispatcher agent implementation
def process_user_message(user_message: str) -> str:
    # 1. Send to dispatcher agent
    dispatcher_result = dispatcher_agent.run_sync(user_message)

    # 2. Extract routing decisions
    if isinstance(dispatcher_result.data, dict) and "target_agent" in dispatcher_result.data:
        target_agent = dispatcher_result.data["target_agent"]
        target_message = dispatcher_result.data["message"]

        # 3. Route to specialized agent
        agent_result = pai_agents[target_agent].run_sync(
            target_message,
            # Pass message history for context
            message_history=dispatcher_result.messages
        )

        # 4. Process the result
        return format_response(agent_result)

    # Default response if no routing
    return dispatcher_result.data
```

### 2. Agent-to-Agent Communication

```python
# Define a RoutingResult model
class RoutingResult(BaseModel):
    """Result of routing a message between agents."""

    source_agent: str = Field(description="Source agent name")
    target_agent: str = Field(description="Target agent name")
    message: str = Field(description="Message being routed")
    response: str = Field(description="Response from target agent")

# Implement routing through tools
@dispatcher_agent.tool
def route_to_agent(ctx: RunContext[Any], target_agent: str, message: str) -> RoutingResult:
    """
    Route a message to another agent for processing.

    Args:
        target_agent: The name of the target agent
        message: The message to send to the agent

    Returns:
        The response from the target agent and routing information
    """
    # Check if target agent exists
    if target_agent not in pai_agents:
        return RoutingResult(
            source_agent="dispatcher",
            target_agent=target_agent,
            message=message,
            response=f"Error: Agent '{target_agent}' not found"
        )

    # Execute the target agent
    result = pai_agents[target_agent].run_sync(message)

    # Return the result with routing information
    return RoutingResult(
        source_agent="dispatcher",
        target_agent=target_agent,
        message=message,
        response=result.data
    )
```

## Best Practices

### 1. Error Handling

```python
from pydantic_ai.exceptions import ModelRetry

@agent.tool
def retrieve_memory(ctx: RunContext[Any], memory_id: str) -> Dict[str, Any]:
    """Retrieve a memory by ID."""
    try:
        memory = memory_service.get_by_id(memory_id)
        return memory.to_dict()
    except Exception as e:
        # Indicate that the tool should be retried
        raise ModelRetry(f"Error retrieving memory: {str(e)}")
```

### 2. Result Validation

```python
@agent.result_validator
def validate_memory_search(result: MemorySearchResult) -> MemorySearchResult:
    """Validate memory search results."""
    if not result.memories and not result.relation_to_query:
        raise ModelRetry("Empty memory results without explanation")

    # Ensure context makes sense
    if len(result.context) < 10:
        result.context = "No relevant memories found for this query."

    return result
```

### 3. Token Usage Tracking

```python
def execute_with_tracking(agent, message):
    """Execute agent with token usage tracking."""
    result = agent.run_sync(message)

    # Access token usage metrics
    usage = result.usage
    print(f"Total tokens: {usage.total_tokens}")
    print(f"Prompt tokens: {usage.prompt_tokens}")
    print(f"Completion tokens: {usage.completion_tokens}")

    return result
```

## Advanced Features

### 1. Streaming Responses

```python
async def stream_response(agent, message):
    """Stream agent responses as they are generated."""
    async with agent.run_stream(message) as stream:
        async for chunk in stream:
            # Process chunk (e.g., print to console)
            if chunk.has_new_text():
                print(chunk.new_text, end="", flush=True)

        # Get the final result
        final_result = await stream.get_data()
        return final_result
```

### 2. Thinking Mode Agents

```python
# Configure an agent with thinking mode
inner_thought_agent = Agent(
    "anthropic:claude-sonnet-4-5",
    name="inner_thought",
    model_settings=ModelSettings(
        temperature=0.7,
        thinking_mode=True  # Enable thinking mode
    ),
    system_prompt="""
    You are Luna's inner thought process.
    First, think step by step about the situation.
    Then, provide a clear summary of your thoughts.
    """
)
```

### 3. Image Support

```python
from pydantic_ai.messages import ImageUrl

# Function to process images
def process_with_image(agent, text_query, image_path):
    """Process a query with both text and image."""
    # Pass both text and an image to the agent
    result = agent.run_sync([
        text_query,
        ImageUrl(url=f"file://{image_path}")
    ])
    return result
```

## Testing

```python
# Using PydanticAI's model override for testing
from pydantic_ai.models import TestModel

def test_memory_retriever():
    """Test memory retriever agent with a test model."""
    agent = memory_retriever  # Your real agent

    # Create test responses
    test_responses = {
        "What's my favorite color?": {"memories": [{"content": "User likes blue"}]}
    }

    # Create a test model
    test_model = TestModel(responses=test_responses)

    # Test the agent with a model override
    with agent.override(model=test_model):
        result = agent.run_sync("What's my favorite color?")
        assert "blue" in str(result.data["memories"][0]["content"])
```

By following these patterns, you can effectively transition Luna's architecture to leverage PydanticAI while maintaining compatibility with existing systems.
