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
python main.py                # Run the application
python -m pytest tests/       # Run all tests
python -m pytest tests/test_file.py::test_function  # Run a specific test
```

## Code Style Guidelines
- **Python Version**: 3.9+ with type hints
- **Formatting**: PEP8 compliant (4-space indentation)
- **Imports**: Standard lib → third-party → project modules, alphabetically ordered
- **Types**: Use typing annotations for all function signatures and class attributes
- **Naming**:
  - Classes: CamelCase (`ElasticsearchAdapter`, `ConversationService`)
  - Functions/variables: snake_case (`process_message`, `user_service`)
  - Constants: UPPER_SNAKE_CASE (`DEFAULT_HOST`)
- **Documentation**: Docstrings for all classes and functions using triple quotes
- **Error Handling**: Use try/except with specific exceptions, provide informative messages
- **Architecture**: Domain-driven design with clean module organization:
  - `adapters`: External service interfaces
  - `core`: Core application logic
  - `domain`: Business models and tools
  - `services`: Business logic services
  - `system_prompts`: Agent prompts and configuration