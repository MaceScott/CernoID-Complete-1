#!/bin/sh
set -e

# Wait for backend to be ready
until wget -q --spider http://backend:8000/health; do
  echo "Waiting for backend to be ready..."
  sleep 1
done

# Start the application in production mode
echo "Starting in production mode..."
exec npm start