#!/bin/bash
# Script to run the Telegram Bot with proper environment setup

cd "$(dirname "$0")"

# Add project root to PYTHONPATH
export PYTHONPATH="$PWD:$PYTHONPATH"

# Run the bot
python3 packages/telegram/run.py
