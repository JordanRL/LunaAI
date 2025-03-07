#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo -e "${YELLOW}Formatting LunaAI code...${NC}"

# Run isort to organize imports
echo -e "${YELLOW}Organizing imports with isort...${NC}"
python -m isort .

# Run black to format code
echo -e "${YELLOW}Formatting code with black...${NC}"
python -m black .

echo -e "${GREEN}Code formatting complete!${NC}"
