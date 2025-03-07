# CI Pipeline Documentation

This document describes the continuous integration (CI) pipeline for the LunaAI project.

## Overview

The CI pipeline consists of several steps that help maintain code quality:

1. **Code Formatting**: Ensure consistent code style
2. **Linting**: Check for coding issues and enforce standards
3. **Type Checking**: Verify type annotations
4. **Unit Testing**: Test individual components
5. **Integration Testing**: Test component interactions
6. **Coverage Reporting**: Measure test coverage

## Local Development Scripts

The following scripts are available for local development:

### Setup Development Environment

```bash
./scripts/setup_dev.sh
```

This script:
- Creates and activates a Python virtual environment
- Installs all required dependencies
- Sets up git hooks for pre-commit checks

### Format Code

```bash
./scripts/format.sh
```

This script:
- Organizes imports with `isort`
- Formats code with `black`

### Check Code Quality

```bash
./scripts/lint.sh
```

This script:
- Checks import ordering with `isort`
- Checks code formatting with `black`
- Performs static code analysis with `flake8`
- Verifies type annotations with `mypy` (if installed)

### Run Tests

```bash
./scripts/test.sh [--unit|--integration] [--coverage]
```

This script:
- Runs unit tests (`--unit`) or integration tests (`--integration`)
- Generates coverage reports (`--coverage`) if pytest-cov is installed

### Complete CI Check

```bash
./scripts/ci_check.sh
```

This script:
- Runs all linting checks
- Executes unit tests
- Executes integration tests
- Generates coverage reports (if pytest-cov is installed)

## Configuration Files

The following configuration files customize the behavior of the CI tools:

### pyproject.toml

Main configuration file that contains settings for:
- pytest
- mypy
- flake8
- black
- isort

### .flake8

Configuration for flake8 linting:
- Maximum line length
- Files to exclude
- Rules to ignore

### .pre-commit-config.yaml

Configuration for pre-commit git hooks:
- Trailing whitespace check
- File ending fixers
- YAML validation
- Import sorting
- Code formatting
- Linting
- Type checking

## GitHub Workflow

The `.github/workflows/ci.yml` file defines the GitHub Actions CI workflow, which:
1. Runs on pushes to main/master and pull requests
2. Executes all the linting and formatting checks
3. Runs the test suite
4. Reports code coverage

## Adding New Tools

To add a new tool to the CI pipeline:

1. Add the tool to `requirements.txt` in the development dependencies section
2. Update the appropriate script in the `scripts/` directory
3. Add configuration in `pyproject.toml` or create a dedicated config file
4. Update `.pre-commit-config.yaml` if the tool should run as a git hook
5. Update the GitHub workflow file if needed
