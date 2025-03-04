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

# Create backup directory with timestamp
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
check_status "Created backup directory"

# Backup PostgreSQL database
print_message "$YELLOW" "Backing up PostgreSQL database..."
docker compose exec -T db pg_dump -U postgres cernoid > "$BACKUP_DIR/database.sql"
check_status "Database backup completed"

# Backup Redis data
print_message "$YELLOW" "Backing up Redis data..."
docker compose exec -T redis redis-cli SAVE
docker compose cp redis:/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"
check_status "Redis backup completed"

# Backup configuration files
print_message "$YELLOW" "Backing up configuration files..."
cp docker-compose.yml "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"
cp redis.conf "$BACKUP_DIR/"
cp -r init-scripts "$BACKUP_DIR/"
check_status "Configuration files backup completed"

# Create backup archive
print_message "$YELLOW" "Creating backup archive..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
check_status "Backup archive created"

# Clean up temporary directory
rm -rf "$BACKUP_DIR"
check_status "Cleaned up temporary files"

print_message "$GREEN" "Backup completed successfully: $BACKUP_DIR.tar.gz" 