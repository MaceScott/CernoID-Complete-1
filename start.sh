#!/bin/bash

# Function to print colorful messages
print_message() {
    echo -e "\e[1;34m[CernoID]\e[0m $1"
}

print_error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if a service is healthy
check_service_health() {
    local service=$1
    local max_attempts=$2
    local attempt=1

    print_message "Waiting for $service to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            print_success "$service is healthy!"
            return 0
        fi
        print_message "Attempt $attempt/$max_attempts: $service is not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done

    print_error "$service failed to become healthy after $max_attempts attempts"
    return 1
}

# Main startup sequence
main() {
    print_message "Starting CernoID System..."

    # Check if Docker is running
    check_docker

    # Create necessary directories
    mkdir -p logs data/images data/temp models

    # Ensure .env file exists
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_message "Creating .env file from .env.example..."
            cp .env.example .env
        else
            print_error ".env file not found and no .env.example to copy from"
            exit 1
        fi
    fi

    # Pull latest images and build services
    print_message "Building and starting services..."
    docker-compose pull
    docker-compose build --no-cache

    # Start services
    docker-compose up -d

    # Check service health
    services=("db" "redis" "backend" "frontend")
    for service in "${services[@]}"; do
        if ! check_service_health $service 12; then
            print_error "Failed to start $service. Check logs with: docker-compose logs $service"
            docker-compose down
            exit 1
        fi
    done

    print_success "CernoID System is now running!"
    print_message "Access the application at: http://localhost:${DOCKER_FRONTEND_PORT:-3000}"
    print_message "API documentation at: http://localhost:${DOCKER_BACKEND_PORT:-8000}/docs"
    print_message "Use Ctrl+C to stop all services"

    # Keep the script running and handle shutdown gracefully
    trap 'docker-compose down; exit 0' SIGINT SIGTERM
    tail -f logs/app.log
}

main 