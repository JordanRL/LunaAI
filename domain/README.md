# Luna Domain Models

This directory contains the domain models for the Luna project. Domain models represent the core data structures and business logic of the application.

## Directory Structure

- `models/`: Domain model classes
  - `memory.py`: Memory-related data models
  - `emotion.py`: Emotional state models
  - `user.py`: User and relationship models
  - `routing.py`: Routing instruction models
  - `conversation.py`: Conversation models
  - `agent.py`: Agent-related models
  - `tool.py`: Tool-related models
  - `config.py`: Configuration models

## Design Principles

The domain models follow these design principles:

1. **Rich Domain Models**: Models contain both data and behavior related to their domain
2. **Immutability**: Most models are immutable dataclasses
3. **Type Safety**: All models use Python type annotations
4. **Serialization**: Models can serialize to/from dictionaries for persistence
5. **No External Dependencies**: Domain models don't depend on external services

## Usage

Domain models are used by services and core components but don't contain implementation details for persistence or external APIs. They represent the business entities and rules of the Luna system.

Example:

```python
from domain.models.memory import Memory

# Create a memory
memory = Memory(
    content="User enjoys outdoor activities",
    memory_type="semantic",
    importance=7,
    user_id="user123"
)

# Access memory properties
print(memory.content)  # "User enjoys outdoor activities"
print(memory.memory_type)  # "semantic"
```