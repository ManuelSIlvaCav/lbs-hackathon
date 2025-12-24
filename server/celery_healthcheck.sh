#!/bin/sh
# Celery Worker Health Check Script
# This script checks if the Celery worker is responding to inspection commands

set -e

# Check if celery worker process is running and inspect active tasks
# This is more reliable in containerized environments than ping
celery -A celery_app inspect active --timeout=10 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Celery worker is healthy"
    exit 0
else
    echo "Celery worker is not responding"
    exit 1
fi
