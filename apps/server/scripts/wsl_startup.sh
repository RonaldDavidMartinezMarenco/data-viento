#!/bin/bash
#
# WSL Startup Script
# Run this when starting WSL to ensure all services are running
#

echo "Starting Data-Viento services..."

# Start CRON
if ! pgrep -x "cron" > /dev/null; then
    sudo service cron start
    echo "✓ CRON started"
else
    echo "✓ CRON already running"
fi

# Start MySQL
if ! sudo service mysql status > /dev/null 2>&1; then
    sudo service mysql start
    echo "✓ MySQL started"
else
    echo "✓ MySQL already running"
fi

# Verify services
echo ""
echo "Service Status:"
sudo service cron status | grep -o "cron is running" || echo "  CRON: stopped"
sudo service mysql status | grep -o "MySQL is running" || echo "  MySQL: stopped"

echo ""
echo "All systems ready! 🚀"