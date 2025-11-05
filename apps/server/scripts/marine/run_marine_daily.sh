SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs/marine_update"

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
LOG_FILE="$LOG_DIR/hourly_$(date +%Y%m%d).log"

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
echo "Marine Hourly Update - $(date)" >> "$LOG_FILE"
echo "==================================================================" >> "$LOG_FILE"

cd "$PROJECT_DIR"
python3 -m src.tasks.updates.marine_update_task --hourly-only --forecast-days 3 >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Marine hourly update completed successfully" >> "$LOG_FILE"
else
    echo "✗ Marine hourly update failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

find "$LOG_DIR" -name "hourly_*.log" -type f -mtime +7 -delete

exit $EXIT_CODE
