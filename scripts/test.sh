#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Parse command line arguments
TEST_PATH="tests/"
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_PATH="tests/unit/"
            shift
            ;;
        --integration)
            TEST_PATH="tests/integration/"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        *)
            # If not a flag, treat as test path
            if [[ $1 != -* ]]; then
                TEST_PATH=$1
            fi
            shift
            ;;
    esac
done

echo -e "${YELLOW}Running tests for LunaAI...${NC}"

# Building the pytest command
PYTEST_CMD="python -m pytest $TEST_PATH -v"

if [ "$COVERAGE" = true ]; then
    # Check if pytest-cov is installed by trying to import it directly
    if pip list | grep -q pytest-cov; then
        PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term --cov-report=html"
        echo -e "${YELLOW}Running tests with coverage...${NC}"
    else
        echo -e "${YELLOW}pytest-cov not installed, running without coverage...${NC}"
        # Set coverage to false so we don't try to use coverage flags
        COVERAGE=false
    fi
fi

# Execute the tests
$PYTEST_CMD
TEST_EXIT=$?

# Check test result
if [ $TEST_EXIT -ne 0 ]; then
    echo -e "${RED}Tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"

    # Show coverage info if enabled
    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}Coverage report generated in htmlcov/index.html${NC}"
    fi
fi
