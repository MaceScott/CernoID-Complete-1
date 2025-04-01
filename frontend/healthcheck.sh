#!/bin/sh

# Exit on any error
set -e

# Maximum number of retries
MAX_RETRIES=3
RETRY_INTERVAL=5
CURRENT_TRY=1

# Function to check health
check_health() {
    echo "Starting health check attempt $CURRENT_TRY..."

    # First check if the process is running
    if ! pgrep -f "node" > /dev/null; then
        echo "Node process is not running"
        return 1
    fi
    echo "✓ Node process is running"

    # Check if port 3000 is listening
    if ! netstat -tln | grep -q ':3000'; then
        echo "Port 3000 is not listening"
        return 1
    fi
    echo "✓ Port 3000 is listening"

    # Try to access the health endpoint
    echo "Checking API health endpoint..."
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000/api/health || echo "000")
    echo "Health endpoint response code: $response"

    if [ "$response" = "200" ]; then
        echo "✓ Health check passed"
        return 0
    else
        echo "✗ Health check failed with response code: $response"
        return 1
    fi
}

# Initial wait for application startup
echo "Waiting for initial startup (10s)..."
sleep 10

# Retry loop
while [ $CURRENT_TRY -le $MAX_RETRIES ]; do
    if check_health; then
        exit 0
    fi
    
    echo "Health check attempt $CURRENT_TRY of $MAX_RETRIES failed. Waiting $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
    CURRENT_TRY=$((CURRENT_TRY + 1))
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1

# Check if the frontend is running and responding
curl -f http://localhost:3000/api/health || exit 1

# Check if the frontend can reach the backend
curl -f http://backend:8000/health || exit 1

# Check if static files are being served
curl -f http://localhost:3000/_next/static || exit 1

# Check if the frontend can access the database through the backend
curl -f http://localhost:3000/api/health/db || exit 1

exit 0 