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

echo -e "${YELLOW}Running linting checks on LunaAI code...${NC}"

# Run isort
echo -e "${YELLOW}Running isort to check imports...${NC}"
python -m isort --check --diff .
ISORT_EXIT=$?

# Run black
echo -e "${YELLOW}Running black to check formatting...${NC}"
python -m black --check .
BLACK_EXIT=$?

# Run flake8
echo -e "${YELLOW}Running flake8 to check style...${NC}"
python -m flake8 .
FLAKE8_EXIT=$?

# Run mypy (if installed)
echo -e "${YELLOW}Running mypy to check types...${NC}"
if python -c "import mypy" 2>/dev/null; then
    python -m mypy .
    MYPY_EXIT=$?
else
    echo -e "${YELLOW}Mypy not installed, skipping type checking${NC}"
    MYPY_EXIT=0 # Don't fail if mypy isn't installed
fi

# Check if any linting check failed
if [ $ISORT_EXIT -ne 0 ] || [ $BLACK_EXIT -ne 0 ] || [ $FLAKE8_EXIT -ne 0 ] || [ $MYPY_EXIT -ne 0 ]; then
    echo -e "${RED}Linting checks failed!${NC}"

    if [ $ISORT_EXIT -ne 0 ]; then
        echo -e "${RED}Fix imports with: python -m isort .${NC}"
    fi

    if [ $BLACK_EXIT -ne 0 ]; then
        echo -e "${RED}Fix formatting with: python -m black .${NC}"
    fi

    exit 1
else
    echo -e "${GREEN}All linting checks passed!${NC}"
fi
