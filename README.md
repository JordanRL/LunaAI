# LunaAI

LunaAI is a multi-agent personality system designed to produce the most human-like simulation of consciousness possible in conversation with modern LLMs.

## Features

- **Multi-Agent Architecture**: Specialized agents handling different aspects of cognition and conversation
- **Emergent Behaviors**: Carefully structured system prompts, agent design, and tools allowing for emergent consciousness-like behaviors
- **Emotion Processing**: Simulation of emotional responses and relationship development
- **Memory Systems**: Short and long-term memory mechanisms for contextual awareness
- **Self-Reflection**: Internal thought processes for deeper reasoning capabilities
- **Persona Evolution**: Dynamic personality development based on interactions
- **Multi-Provider Support**: Flexible adapter interface supporting multiple LLM providers

## LLM Provider Support

Luna now supports multiple LLM providers through a unified adapter interface:

- **Anthropic**: Claude models (default)
- **OpenAI**: GPT-4 models
- **Google**: Gemini models

You can easily switch between providers by setting the `PROVIDER` environment variable:

```bash
# Use Anthropic Claude (default)
export PROVIDER=anthropic

# Use OpenAI GPT
export PROVIDER=openai

# Use Google Gemini
export PROVIDER=gemini
```

### Provider Feature Comparison

| Feature | Anthropic | OpenAI | Gemini |
|---------|-----------|--------|--------|
| Text Generation | ✅ | ✅ | ✅ |
| Tool Calling | ✅ | ✅ | ✅ |
| System Instructions | ✅ | ✅ | ✅ |
| Content Blocks | ✅ | ❌ | ✅ |
| Thinking Blocks | ✅ | ❌ | ❌ |
| Image Input | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ |

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/luna-ai.git
cd luna-ai

# Set up development environment
./scripts/setup_dev.sh

# Set up your API keys (for the providers you want to use)
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here

# Set your preferred provider (optional, defaults to anthropic)
export PROVIDER=anthropic
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

# Compare responses from different LLM providers
./scripts/compare_adapters.py "Your question here?"

# Compare providers with tools enabled
./scripts/compare_adapters.py "Calculate 25 * 16" --with-tools
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
