#!/bin/bash
# Update daily forecast only (runs once per day)

cd "$(dirname "$0")/.." || exit 1
python3 -m src.tasks.weather_update_task --daily-only
exit $?