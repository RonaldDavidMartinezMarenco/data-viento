#!/bin/bash
#
# Air Quality Data Cleanup Script
# Runs weekly to delete old air quality forecasts
#
# Schedule: 0 3 * * 0 (Sunday at 3 AM)
# Log: /home/ronald/data-viento/apps/server/logs/cleanup/air_quality_YYYYMMDD.log

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs/cleanup"


# VIRTUAL ENVIRONMENT ACTIVATION
VENV_PATH="$PROJECT_DIR/.venv"  # or wherever your venv is

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ Virtual environment activated: $VENV_PATH" >> "$LOG_DIR/current_$(date +%Y%m%d).log"
else
    echo "✗ Virtual environment not found at: $VENV_PATH" >> "$LOG_DIR/current_$(date +%Y%m%d).log"
    exit 1
fi

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/air_quality_$(date +%Y%m%d).log"

if ! sudo service mysql status > /dev/null 2>&1; then
    echo "✗ MySQL is not running. Starting MySQL..." >> "$LOG_FILE"
    sudo service mysql start >> "$LOG_FILE" 2>&1
    
    # Wait for MySQL to be ready
    sleep 3
    
    if ! sudo service mysql status > /dev/null 2>&1; then
        echo "✗ Failed to start MySQL. Exiting." >> "$LOG_FILE"
        exit 1
    fi
    echo "✓ MySQL started successfully" >> "$LOG_FILE"
fi

if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
    echo "✓ Environment variables loaded from .env" >> "$LOG_FILE"
else
    echo "✗ .env file not found at $PROJECT_DIR/.env" >> "$LOG_FILE"
    exit 1
fi

echo "==================================================================" >> "$LOG_FILE"
echo "Air Quality Cleanup - $(date)" >> "$LOG_FILE"
echo "==================================================================" >> "$LOG_FILE"

cd "$PROJECT_DIR"
# Keep 30 days of air quality data
python3 -m src.tasks.cleanups.cleanup_task_air_quality --days 30 >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Air quality cleanup completed successfully" >> "$LOG_FILE"
else
    echo "✗ Air quality cleanup failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

find "$LOG_DIR" -name "air_quality_*.log" -type f -mtime +90 -delete

exit $EXIT_CODE

