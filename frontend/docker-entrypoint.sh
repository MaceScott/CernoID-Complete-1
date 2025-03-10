#!/bin/sh
set -e

# Wait for backend to be ready
until wget -q -O - http://backend:8000/health >/dev/null 2>&1; do
  echo "Waiting for backend to be ready..."
  sleep 2
done

# Start the application
if [ "$NODE_ENV" = "development" ]; then
  echo "Starting in development mode..."
  exec npm run dev
else
  echo "Starting in production mode..."
  exec npm start
fi 