#!/bin/bash
# Update hourly forecast only (runs every 3 hours)

cd "$(dirname "$0")/.." || exit 1
python3 -m src.tasks.weather_update_task --hourly-only 
exit $?

