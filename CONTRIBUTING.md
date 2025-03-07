# Contributing to LunaAI

Thank you for your interest in contributing to LunaAI! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/luna-ai.git
   cd luna-ai
   ```

2. Set up the development environment:
   ```bash
   ./scripts/setup_dev.sh
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

## Development Process

### Code Style

LunaAI follows PEP 8 coding standards with additional requirements:

- Use Python 3.9+ features and type hints
- Format code with `black` and sort imports with `isort`
- Add proper docstrings to all classes and functions
- Follow the domain-driven design architecture
- Maintain 100% test coverage for new features

You can run the formatting tools with:
```bash
./scripts/format.sh
```

### Testing

All code changes should include appropriate tests. We use `pytest` for testing:

- Unit tests for individual functions and classes
- Integration tests for interactions between components

To run tests:
```bash
# Run all tests
./scripts/test.sh

# Run only unit or integration tests
./scripts/test.sh --unit
./scripts/test.sh --integration

# Run with coverage reporting
./scripts/test.sh --coverage
```

### Pull Request Process

1. Create a branch for your feature or bugfix
2. Implement your changes with tests
3. Ensure all tests pass and code meets style requirements
4. Update documentation if needed
5. Submit a pull request with a clear description of the changes

Your pull request should:
- Have a clear, descriptive title
- Explain what the change does
- Include any relevant issue numbers
- Describe how you tested the change
- Include screenshots for UI changes (if applicable)

## Architecture Overview

When contributing, please keep in mind our architecture:

- **Domain-Driven Design**: Core business logic and models are in the `domain` module
- **Adapters Pattern**: External services are accessed through adapters
- **Service Layer**: Business logic is organized into services
- **Multi-Agent System**: The system is composed of specialized agents with specific responsibilities

## Reporting Issues

When reporting issues, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment information (OS, Python version, etc.)

## License

By contributing to LunaAI, you agree that your contributions will be licensed under the project's MIT License.
