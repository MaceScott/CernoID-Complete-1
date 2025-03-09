#!/bin/bash

# Exit on error
set -e

# Configuration
BACKUP_DIR="./backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="cernoid-complete-1-db-1"
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-cernoid}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to print messages
echo_message() {
    echo "[BACKUP] $1"
}

# Backup database
backup_database() {
    echo_message "Creating database backup..."
    docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    echo_message "Database backup created at: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
}

# Backup configuration files
backup_config() {
    echo_message "Backing up configuration files..."
    
    # Create config backup directory
    mkdir -p "$BACKUP_DIR/config_$TIMESTAMP"
    
    # Backup .env file if it exists
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/config_$TIMESTAMP/"
    fi
    
    # Backup docker-compose.yml
    cp docker-compose.yml "$BACKUP_DIR/config_$TIMESTAMP/"
    
    echo_message "Configuration backup created at: $BACKUP_DIR/config_$TIMESTAMP/"
}

# Backup models and face encodings
backup_models() {
    echo_message "Backing up models and face encodings..."
    
    # Create models backup directory
    mkdir -p "$BACKUP_DIR/models_$TIMESTAMP"
    
    # Backup models if they exist
    if [ -d "backend/models" ]; then
        cp -r backend/models/* "$BACKUP_DIR/models_$TIMESTAMP/"
    fi
    
    echo_message "Models backup created at: $BACKUP_DIR/models_$TIMESTAMP/"
}

# Cleanup old backups (keep last 5)
cleanup_old_backups() {
    echo_message "Cleaning up old backups..."
    
    # Keep only last 5 database backups
    ls -t "$BACKUP_DIR"/db_backup_* 2>/dev/null | tail -n +6 | xargs -r rm
    
    # Keep only last 5 config backups
    ls -td "$BACKUP_DIR"/config_* 2>/dev/null | tail -n +6 | xargs -r rm -rf
    
    # Keep only last 5 model backups
    ls -td "$BACKUP_DIR"/models_* 2>/dev/null | tail -n +6 | xargs -r rm -rf
}

# Create compressed archive of all backups
create_archive() {
    echo_message "Creating compressed archive..."
    tar -czf "$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz" \
        "$BACKUP_DIR/db_backup_$TIMESTAMP.sql" \
        "$BACKUP_DIR/config_$TIMESTAMP" \
        "$BACKUP_DIR/models_$TIMESTAMP"
    echo_message "Archive created at: $BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz"
}

# Main backup process
main() {
    echo_message "Starting backup process..."
    
    backup_database
    backup_config
    backup_models
    create_archive
    cleanup_old_backups
    
    echo_message "Backup process completed successfully!"
}

# Run main backup process
main "$@" 