#!/bin/sh

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
    sleep 1
done
echo "Database is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "Redis is ready!"

# Check if model files exist
if [ ! -f "$SHAPE_PREDICTOR_MODEL" ]; then
    echo "Error: Shape predictor model not found at $SHAPE_PREDICTOR_MODEL"
    exit 1
fi

if [ ! -f "$LIVENESS_MODEL_PATH" ]; then
    echo "Error: Liveness model not found at $LIVENESS_MODEL_PATH"
    exit 1
fi

# Create required directories if they don't exist
mkdir -p /var/log/cernoid
mkdir -p /etc/cernoid/secrets

# Set proper permissions
chmod 755 /var/log/cernoid
chmod 755 /etc/cernoid/secrets

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting the application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info 