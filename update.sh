#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if a command was successful
check_status() {
    if [ $? -eq 0 ]; then
        print_message "✓ $1" "$GREEN"
    else
        print_message "✗ $1" "$RED"
        exit 1
    fi
}

# Function to update a specific service
update_service() {
    local service=$1
    print_message "Updating $service..." "$YELLOW"
    
    # Pull the latest image
    docker compose pull $service
    check_status "Pulled latest image for $service"
    
    # Update the service
    docker compose up -d --no-deps $service
    check_status "Updated $service"
    
    # Wait for health check
    print_message "Waiting for $service to be healthy..." "$YELLOW"
    docker compose ps $service | grep "healthy" > /dev/null
    check_status "$service is healthy"
}

# Function to update all services
update_all() {
    print_message "Starting full system update..." "$YELLOW"
    
    # Create backup of current state
    print_message "Creating backup of current state..." "$YELLOW"
    docker compose ps > backup_state.txt
    check_status "Backup created"
    
    # Update services in order
    update_service "db"
    update_service "redis"
    update_service "backend"
    update_service "frontend"
    
    # Clean up old images
    print_message "Cleaning up old images..." "$YELLOW"
    docker image prune -f
    check_status "Cleaned up old images"
    
    print_message "Full system update completed successfully!" "$GREEN"
}

# Check if a specific service is provided
if [ -n "$1" ]; then
    # Update specific service
    update_service "$1"
else
    # Update all services
    update_all
fi 