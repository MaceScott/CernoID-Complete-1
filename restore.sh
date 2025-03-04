#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Print message with color
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if command was successful
check_status() {
    if [ $? -eq 0 ]; then
        print_message "$GREEN" "✓ $1"
    else
        print_message "$RED" "✗ $1"
        exit 1
    fi
}

# Check if backup file is provided
if [ -z "$1" ]; then
    print_message "$RED" "Error: Please provide a backup file path"
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_message "$RED" "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create temporary restore directory
RESTORE_DIR="restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESTORE_DIR"
check_status "Created restore directory"

# Extract backup archive
print_message "$YELLOW" "Extracting backup archive..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
check_status "Backup archive extracted"

# Stop services
print_message "$YELLOW" "Stopping services..."
docker compose down
check_status "Services stopped"

# Restore configuration files
print_message "$YELLOW" "Restoring configuration files..."
cp "$RESTORE_DIR/docker-compose.yml" ./
cp "$RESTORE_DIR/.env" ./
cp "$RESTORE_DIR/redis.conf" ./
rm -rf init-scripts
cp -r "$RESTORE_DIR/init-scripts" ./
check_status "Configuration files restored"

# Start services
print_message "$YELLOW" "Starting services..."
docker compose up -d db redis
check_status "Database and Redis services started"

# Wait for services to be healthy
print_message "$YELLOW" "Waiting for services to be healthy..."
sleep 10

# Restore PostgreSQL database
print_message "$YELLOW" "Restoring PostgreSQL database..."
docker compose exec -T db psql -U postgres -d cernoid < "$RESTORE_DIR/database.sql"
check_status "Database restored"

# Restore Redis data
print_message "$YELLOW" "Restoring Redis data..."
docker compose cp "$RESTORE_DIR/redis_dump.rdb" redis:/data/dump.rdb
docker compose restart redis
check_status "Redis data restored"

# Start remaining services
print_message "$YELLOW" "Starting remaining services..."
docker compose up -d
check_status "All services started"

# Clean up temporary directory
rm -rf "$RESTORE_DIR"
check_status "Cleaned up temporary files"

print_message "$GREEN" "Restore completed successfully" 