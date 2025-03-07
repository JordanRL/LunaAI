#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up development environment for LunaAI...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -U pip
pip install -r requirements.txt

# Setup git hooks using pre-commit if available
if command -v pre-commit >/dev/null 2>&1; then
    echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
    pre-commit install
fi

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${GREEN}To activate the environment, run: source venv/bin/activate${NC}"
