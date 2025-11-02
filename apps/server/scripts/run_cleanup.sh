#!/bin/bash

# Daily cleanup script
# Cleans up old forecast data

cd "$(dirname "$0")/.." || exit 1

echo "Running cleanup task..."
python3 -m src.tasks.cleanup_task --days-to-keep 5 --hours-to-keep 120

exit $?
