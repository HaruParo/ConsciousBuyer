#!/bin/bash

# Set the Python path to include the src directory
export PYTHONPATH="${PYTHONPATH}:$(dirname "$0")/src"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the Streamlit app
streamlit run src/ui/app.py "$@"
