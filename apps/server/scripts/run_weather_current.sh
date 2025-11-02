#!/bin/bash
# Update current weather only (runs every 15 min)

cd "$(dirname "$0")/.." || exit 1
echo "DIRECTORY (SERVER_DIR): $(pwd)"
python3 -m src.tasks.weather_update_task --current-only
exit $?


