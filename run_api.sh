#!/bin/bash

# Run the Expense Tracker API
# This script ensures the Python path is set correctly

cd "$(dirname "$0")"

echo "Starting Expense Tracker API..."
PYTHONPATH="$(pwd):$PYTHONPATH" python packages/api/run.py
