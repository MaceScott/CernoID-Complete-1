#!/bin/sh
set -e

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
while ! nc -z backend 8000; do
  sleep 1
done
echo "Backend is ready!"

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# Start the application
echo "Starting Next.js application..."
exec npm start