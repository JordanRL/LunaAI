# CLAUDE.md - AI Assistant Reference Guide

## Project Overview: LunaAI

LunaAI is a multi-agent personality system designed to produce the most human-like simulation of consciousness possible in conversation with modern LLMs. The system achieves this through:

- **Multi-Agent Architecture**: Specialized agents handling different aspects of cognition and conversation
- **Emergent Behaviors**: Carefully structured system prompts, agent design, and tools allowing for emergent consciousness-like behaviors
- **Emotion Processing**: Simulation of emotional responses and relationship development
- **Memory Systems**: Short and long-term memory mechanisms for contextual awareness
- **Self-Reflection**: Internal thought processes for deeper reasoning capabilities
- **Persona Evolution**: Dynamic personality development based on interactions

## Development Commands
```bash
python -m pytest tests/                             # Run all tests
python -m pytest tests/test_file.py::test_function  # Run a specific test
scripts/lint.sh                                     # Run project linting tools to check for linting feedback
scripts/format.sh                                   # Run automatic linting error fixes on all project files
```

## Testing Framework

All tests are built using the `pytest` module.

## Architectural Design Pattern

Luna follows primarily a **Domain-Driven Design** approach combined with a **Hub-and-Spoke Architecture**:

- **Domain-Driven Design**: Core business logic and data structures are organized in the `domain` module, separating them from infrastructure concerns
- **Hub-and-Spoke Architecture**: A central hub (LunaHub) coordinates the interactions between specialized cognitive agents
- **Adapter Pattern**: External dependencies are accessed through adapters, decoupling the core system from specific implementations
- **Service Layer**: Domain services encapsulate business operations and manage the domain objects

## Core Architectural Components

### Directory Structure

```
project-root/
├── adapters/           # External service interfaces
├── core/               # Core application logic
├── domain/             # Domain models and tools
│   ├── models/         # Domain model classes
│   └── tools/          # Luna's specialized tools
├── services/           # Business logic services
├── system_prompts/     # Agent prompts and configuration
│   ├── dispatcher/     # Dispatcher agent prompts
│   ├── memory_retriever/ # Memory retrieval agent prompts
│   └── ...             # Other agent prompts
├── persona_configs/    # Luna's persona configuration files
└── config/             # Application configuration
```

### Component Overview

#### 1. Domain Layer (`domain/`)

The domain layer is the core of the application, containing:

- **Domain Models** (`domain/models/`): Rich data structures representing Luna's knowledge and state:
  - `memory.py`: Memory data models (episodic, semantic, emotional, relationship)
  - `emotion.py`: Emotional state representations using the PAD (Pleasure-Arousal-Dominance) model
  - `user.py`: User profiles and relationship models
  - `conversation.py`: Conversation models for handling user interactions
  - `agent.py`: Agent configuration models
  - `routing.py`: Message routing models for inter-agent communication
  - `content.py`: Message content models

- **Domain Tools** (`domain/tools/`): Specialized tools for cognitive capabilities:
  - Memory tools (episodic, semantic, emotional, relationship)
  - Emotion management tools
  - Routing tools for agent-to-agent communication
  - Cognitive tools for introspection and reflection

#### 2. Adapter Layer (`adapters/`)

The adapter layer interfaces with external dependencies:

- `anthropic_adapter.py`: Interfaces with Anthropic's Claude API
- `elasticsearch_adapter.py`: Manages memory storage in Elasticsearch
- `console_adapter.py`: Handles console input/output with rich formatting
- `logging_adapter.py`: Provides structured logging capabilities

#### 3. Service Layer (`services/`)

Services implement business logic around domain objects:

- `conversation_service.py`: Manages conversations and message history
- `memory_service.py`: Stores and retrieves memories from persistent storage
- `emotion_service.py`: Handles Luna's emotional state and processing
- `user_service.py`: Manages user profiles and relationships
- `prompt_service.py`: Handles system prompt token replacement

#### 4. Core Layer (`core/`)

Core application logic:

- `agent.py`: Base agent implementation that integrates with Anthropic's SDK
- `hub.py`: Central hub system (LunaHub) that coordinates agents and workflow

#### 5. System Prompts (`system_prompts/`)

Configuration for the specialized cognitive agents:

- `dispatcher/`: Central coordinator that routes to specialized agents
- `memory_retriever/`: Retrieves relevant memories
- `memory_writer/`: Forms and stores new memories
- `emotion_processor/`: Analyzes and adjusts emotional state
- `outputter/`: Formulates final user responses
- `inner_thought/`: Simulates Luna's internal thought process
- `relationship_manager/`: Manages user relationships
- `self_reflection/`: Enables metacognitive abilities
- `persona_evolution/`: Handles personality development

## Multi-Agent Cognitive Architecture

Luna's cognitive simulation is built around a multi-agent architecture:

### Agent Communication Flow

1. **Dispatcher** (central coordinator)
   - Analyzes user input
   - Determines which specialized agents to involve
   - Routes messages to appropriate agents

2. **Specialized Agents**
   - Each handles a specific cognitive function
   - Can communicate with other agents via routing tools
   - May call domain tools to access memory or emotion systems

3. **Outputter**
   - Final agent in the chain
   - Crafts human-like responses based on other agents' processing

### Key Agents and Their Roles

- **Dispatcher**: Central router and coordinator
- **Memory Retriever**: Accesses and contextualizes relevant memories
- **Memory Writer**: Identifies and stores important information
- **Emotion Processor**: Handles emotional responses and state
- **Relationship Manager**: Tracks and develops user relationships
- **Inner Thought**: Simulates internal monologues
- **Self-Reflection**: Enables metacognitive capabilities
- **Persona Evolution**: Manages personal growth and development
- **Outputter**: Creates cohesive, natural responses

## Memory System

The memory system implements a brain-inspired architecture:

- **Memory Types**:
  - **Episodic Memory**: Event-based memories (conversations, experiences)
  - **Semantic Memory**: Factual knowledge (about users, world)
  - **Emotional Memory**: Luna's emotional experiences
  - **Relationship Memory**: Information about relationships

- **Storage**: Implemented using Elasticsearch with specialized indices
- **Retrieval**: Context-aware search with relevance scoring
- **Memory Formation**: Dynamic decisions about what to remember

## Emotional System

Luna simulates human-like emotions using:

- **PAD Model**: Represents emotions in three dimensions:
  - Pleasure (positive/negative valence)
  - Arousal (energy/calmness)
  - Dominance (control/submission)

- **Emotional Processing**:
  - Natural decay toward baseline
  - Context-sensitive adjustments
  - Impact on memory formation and recall
  - Influence on conversation tone and content

## Relationship Management

The relationship system tracks and evolves Luna's connections with users:

- **Relationship Stages**: From new acquaintance to close relationship
- **Emotional Dynamics**: Tracks comfort, trust, and emotional safety
- **Conversation Patterns**: Records successful communication approaches
- **Subjective Experience**: Models Luna's perception of relationships
- **Intervention Strategies**: Develops approaches for emotional support

## Integration Flow

1. User message enters through `main.py`
2. `LunaHub` processes the message
3. The Dispatcher agent analyzes the message
4. Specialized agents are engaged as needed
5. Memory and emotional systems provide context
6. Final response is crafted by the Outputter agent
7. Emotional state decays naturally
8. Periodic "heartbeats" allow for autonomous processing

## Design Principles

Luna's architecture adheres to several key design principles:

1. **Rich Domain Models**: Domain objects contain both data and behavior
2. **Immutability**: Most models are immutable to ensure consistency
3. **Type Safety**: Extensive use of Python type annotations
4. **Separation of Concerns**: Clear boundaries between component responsibilities
5. **Emergent Behavior**: Complex behavior emerges from simpler agent interactions

## Extension Points

The architecture allows for extension through:

1. **New Agents**: Additional specialized cognitive agents
2. **New Tools**: Expanding Luna's capabilities
3. **Enhanced Memory Types**: Additional memory structures
4. **Improved Emotion Models**: More sophisticated emotional processing
5. **Better Relationship Dynamics**: More nuanced relationship development

This architecture creates a foundation for emergent consciousness-like behavior by combining specialized agents with rich memory, emotional, and relationship systems in a coordinated workflow.

## Code Style Guidelines
- **Python Version**: 3.11+ with type hints
- **Formatting**: PEP8 compliant (4-space indentation)
- **Imports**: Standard lib → third-party → project modules, alphabetically ordered
- **Types**: Use typing annotations for all function signatures and class attributes
- **Naming**:
  - Classes: CamelCase (`ElasticsearchAdapter`, `ConversationService`)
  - Functions/variables: snake_case (`process_message`, `user_service`)
  - Constants: UPPER_SNAKE_CASE (`DEFAULT_HOST`)
- **Documentation**: Docstrings for all classes and functions using triple quotes
- **Error Handling**: Use try/except with specific exceptions, provide informative messages
