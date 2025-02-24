#!/bin/bash
# Quick start script for CernoID

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "Please edit .env with your settings"
    exit 1
fi

# Start services
docker-compose up -d

echo "CernoID is starting..."
echo "Access the application at http://localhost:8000"
