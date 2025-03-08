#!/bin/bash
set -e

# Function to check GPU availability (only once)
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU is available"
        return 0
    else
        echo "GPU is not available, running in CPU mode"
        return 1
    fi
}

# Function to wait for database to be ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    max_retries=30
    retries=0

    while [ $retries -lt $max_retries ]; do
        if PGPASSWORD=postgres psql -h db -U postgres -d cernoid -c 'SELECT 1;' 2>&1; then
            echo "Database is ready"
            return 0
        else
            retries=$((retries + 1))
            echo "Database is unavailable - retry $retries of $max_retries"
            echo "Connection error details:"
            PGPASSWORD=postgres psql -h db -U postgres -d cernoid -c 'SELECT 1;' 2>&1 || true
            sleep 2
        fi
    done

    echo "Error: Database connection timeout after $max_retries attempts"
    exit 1
}

# Function to wait for Redis to be ready
wait_for_redis() {
    echo "Waiting for Redis to be ready..."
    max_retries=30
    retries=0

    while [ $retries -lt $max_retries ]; do
        if redis-cli -h redis ping > /dev/null 2>&1; then
            echo "Redis is ready"
            return 0
        fi
        retries=$((retries + 1))
        echo "Redis is unavailable - retry $retries of $max_retries"
        sleep 2
    done

    echo "Error: Redis connection timeout after $max_retries attempts"
    exit 1
}

# Check GPU availability once and store the result
GPU_AVAILABLE=0
if check_gpu; then
    GPU_AVAILABLE=1
fi

# Wait for dependencies
wait_for_db
wait_for_redis

echo "Database is up - executing migrations"

# Run database migrations
alembic upgrade head

# Start the application
if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting application in development mode..."
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
else
    echo "Starting application in production mode..."
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
fi 