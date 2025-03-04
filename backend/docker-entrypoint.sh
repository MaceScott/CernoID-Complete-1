#!/bin/bash
set -e

# Wait for database to be ready
until pg_isready -h db -U postgres -d cernoid; do
  echo "Waiting for database to be ready..."
  sleep 2
done

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
if [ "$ENVIRONMENT" = "development" ]; then
  echo "Starting in development mode..."
  exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Starting in production mode..."
  exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
fi 