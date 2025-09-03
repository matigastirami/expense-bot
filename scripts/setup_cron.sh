#!/bin/bash

# Setup cron job to process pending transactions every 2 hours
SCRIPT_PATH="/app/src/scripts/process_pending_transactions.py"
LOG_PATH="/var/log/pending_transactions.log"

# Create log directory if it doesn't exist
mkdir -p /var/log

# Add cron job (runs every 2 hours)
CRON_JOB="0 */2 * * * cd /app && python $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added: Process pending transactions every 2 hours"
    echo "📝 Logs will be written to: $LOG_PATH"
else
    echo "ℹ️ Cron job already exists"
fi

# Show current crontab
echo "Current cron jobs:"
crontab -l