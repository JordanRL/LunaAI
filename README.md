# LunaAI

LunaAI is a multi-agent personality system designed to produce the most human-like simulation of consciousness possible in conversation with modern LLMs.

## Features

- **Multi-Agent Architecture**: Specialized agents handling different aspects of cognition and conversation
- **Emergent Behaviors**: Carefully structured system prompts, agent design, and tools allowing for emergent consciousness-like behaviors
- **Emotion Processing**: Simulation of emotional responses and relationship development
- **Memory Systems**: Short and long-term memory mechanisms for contextual awareness
- **Self-Reflection**: Internal thought processes for deeper reasoning capabilities
- **Persona Evolution**: Dynamic personality development based on interactions

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/luna-ai.git
cd luna-ai

# Set up development environment
./scripts/setup_dev.sh
```

## Development

### Code Quality Tools

The project uses several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

### Development Commands

```bash
# Format code
./scripts/format.sh

# Run linting checks
./scripts/lint.sh

# Run tests
./scripts/test.sh

# Run specific test sets
./scripts/test.sh --unit
./scripts/test.sh --integration

# Run tests with coverage
./scripts/test.sh --coverage
```

## Project Structure

- `adapters/`: External service interfaces
- `core/`: Core application logic
- `domain/`: Business models and tools
  - `models/`: Domain model classes
  - `tools/`: Specialized tools for different capabilities
- `services/`: Business logic services
- `system_prompts/`: Agent prompts and configuration
- `config/`: Application configuration
- `tests/`: Unit and integration tests

## License

[MIT License](LICENSE)
