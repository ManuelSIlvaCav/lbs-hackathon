#!/bin/sh
# Celery Worker Health Check Script
# This script checks if the Celery worker is responding to inspection commands

set -e

# Try to ping the celery worker
# The inspect ping command will return the worker status
celery -A celery_app inspect ping -d "celery@$HOSTNAME" --timeout=10 2>&1 | grep -q "pong"

if [ $? -eq 0 ]; then
    echo "Celery worker is healthy"
    exit 0
else
    echo "Celery worker is not responding"
    exit 1
fi
