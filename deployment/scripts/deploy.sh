#!/bin/bash

# Check if running in production mode
if [ "$1" == "prod" ]; then
    echo "Deploying in production mode..."
    ENVIRONMENT="prod"
else
    echo "Deploying in development mode..."
    ENVIRONMENT="dev"
fi

# Load environment variables
source .env.$ENVIRONMENT

# Build Docker images
echo "Building Docker images..."
docker-compose -f deployment/docker-compose.yml build

# Start services
echo "Starting services..."
docker-compose -f deployment/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose -f deployment/docker-compose.yml exec face-recognition-api \
    python3 -m alembic upgrade head

# Check service health
echo "Checking service health..."
curl -f http://localhost:8000/health || exit 1

echo "Deployment completed successfully!" 