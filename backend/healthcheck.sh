#!/bin/bash
set -e

# Check if the application is running
if ! nc -z localhost 8000; then
    echo "Application is not running"
    exit 1
fi

# Check if the application is responding
if ! curl -f http://localhost:8000/health; then
    echo "Application is not responding"
    exit 1
fi

exit 0 