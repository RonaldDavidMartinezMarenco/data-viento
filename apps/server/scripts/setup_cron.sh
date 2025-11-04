#!/bin/bash

# Setup cron jobs for automated tasks
# Uses extraction frequencies from src/constants/open_meteo_params.py

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up cron jobs based on EXTRACTION_FREQUENCIES..."
echo "Server directory: $SERVER_DIR"

# Create crontab entries
cat > /tmp/data-viento-cron << 'EOF'
# ============================================================================
# Data-Viento Automated Tasks
# Based on EXTRACTION_FREQUENCIES from open_meteo_params.py
# ============================================================================

# -----------------------------------------------------------------------------
# WEATHER DATA UPDATES
# -----------------------------------------------------------------------------

# Current weather: Every 15 minutes (EXTRACTION_FREQUENCIES['current_weather'])
*/15 * * * * cd $SERVER_DIR && python3 -m src.tasks.weather_update_task --current-only >> $SERVER_DIR/logs/weather_update/current.log 2>&1

# Hourly forecast: Every 3 hours (EXTRACTION_FREQUENCIES['weather_hourly'])
0 */3 * * * cd $SERVER_DIR && python3 -m src.tasks.weather_update_task --hourly-only >> $SERVER_DIR/logs/weather_update/hourly.log 2>&1

# Daily forecast: Once per day at 6 AM (EXTRACTION_FREQUENCIES['weather_daily'])
0 6 * * * cd $SERVER_DIR && python3 -m src.tasks.weather_update_task --daily-only >> $SERVER_DIR/logs/weather_update/daily.log 2>&1

# Complete update (current + daily): Twice per day at 6 AM and 6 PM
# Provides backup if individual jobs fail
0 6,18 * * * cd $SERVER_DIR && python3 -m src.tasks.weather_update_task >> $SERVER_DIR/logs/weather_update/complete.log 2>&1

# -----------------------------------------------------------------------------
# DATA CLEANUP
# -----------------------------------------------------------------------------

# Cleanup old forecast data: Daily at 2 AM
0 2 * * * cd $SERVER_DIR && python3 -m src.tasks.cleanup_task --days-to-keep 7 >> $SERVER_DIR/logs/cleanup/daily.log 2>&1

# -----------------------------------------------------------------------------
# FUTURE: AIR QUALITY, MARINE, SATELLITE (to be implemented)
# -----------------------------------------------------------------------------

# Air Quality: Every 12 hours (EXTRACTION_FREQUENCIES['air_quality_current'])
# 0 */12 * * * cd $SERVER_DIR && python3 -m src.tasks.air_quality_update_task >> $SERVER_DIR/logs/air_quality/update.log 2>&1

# Marine: Every 6 hours (EXTRACTION_FREQUENCIES['marine_current'])
# 0 */6 * * * cd $SERVER_DIR && python3 -m src.tasks.marine_update_task >> $SERVER_DIR/logs/marine/update.log 2>&1

# Satellite Radiation: Every day (EXTRACTION_FREQUENCIES['satellite_radiation'])
# 0 6 * * * * cd $SERVER_DIR && python3 -m src.tasks.satellite_update_task >> $SERVER_DIR/logs/satellite/update.log 2>&1

EOF

# Replace $SERVER_DIR placeholder with actual path
sed "s|\$SERVER_DIR|$SERVER_DIR|g" /tmp/data-viento-cron > /tmp/data-viento-cron-final

# Install crontab
crontab -l > /tmp/current-cron 2>/dev/null || true
cat /tmp/current-cron /tmp/data-viento-cron-final | crontab -

echo "✓ Cron jobs installed successfully!"
echo ""
echo "Installed schedules:"
echo "  • Current weather:  Every 15 minutes"
echo "  • Hourly forecast:  Every 3 hours"
echo "  • Daily forecast:   Once per day (6 AM)"
echo "  • Complete update:  Twice per day (6 AM, 6 PM)"
echo "  • Cleanup:          Daily at 2 AM"
echo ""
echo "Current crontab:"
crontab -l | grep -A 100 "Data-Viento"

# Cleanup
rm /tmp/data-viento-cron /tmp/data-viento-cron-final /tmp/current-cron 2>/dev/null || true