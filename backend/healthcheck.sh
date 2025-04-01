#!/bin/sh

# Exit on any error
set -e

# Function to check if a service is ready
check_service() {
    local service=$1
    local host=$2
    local port=$3
    local max_retries=5
    local retry_count=1
    
    echo "Checking $service connection..."
    while [ $retry_count -le $max_retries ]; do
        if nc -z -w 5 "$host" "$port"; then
            echo "$service is ready"
            return 0
        fi
        echo "Waiting for $service to be ready (attempt $retry_count/$max_retries)..."
        sleep 2
        retry_count=$((retry_count + 1))
    done
    echo "$service is not ready after $max_retries attempts"
    return 1
}

# Check if the backend is running and responding
curl -f http://localhost:8000/health || exit 1

# Check if the backend can connect to the database
curl -f http://localhost:8000/health/db || exit 1

# Check if the backend can connect to Redis
curl -f http://localhost:8000/health/redis || exit 1

# Check if model files are present
if [ ! -f "$SHAPE_PREDICTOR_MODEL" ]; then
    echo "Shape predictor model not found at $SHAPE_PREDICTOR_MODEL"
    exit 1
fi

if [ ! -f "$LIVENESS_MODEL_PATH" ]; then
    echo "Liveness model not found at $LIVENESS_MODEL_PATH"
    exit 1
fi

# Check if required directories exist and are writable
for dir in "/var/log/cernoid" "/etc/cernoid/secrets"; do
    if [ ! -d "$dir" ]; then
        echo "Directory $dir does not exist"
        exit 1
    fi
    if [ ! -w "$dir" ]; then
        echo "Directory $dir is not writable"
        exit 1
    fi
done

exit 0 