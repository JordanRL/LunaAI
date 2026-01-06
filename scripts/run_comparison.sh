#!/bin/bash
# Load environment variables from ~/.bashrc
eval "$(grep -E '^export (OPENAI_API_KEY|GEMINI_API_KEY|ANTHROPIC_API_KEY)=' ~/.bashrc)"

# Run the comparison script
cd $(dirname $0)/..
python scripts/compare_adapters.py "$@"
