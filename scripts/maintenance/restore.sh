#!/bin/bash

# Exit on error
set -e

# Configuration
BACKUP_DIR="./backup"
DB_CONTAINER="cernoid-complete-1-db-1"
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-cernoid}

# Function to print messages
echo_message() {
    echo "[RESTORE] $1"
}

# Function to list available backups
list_backups() {
    echo_message "Available backups:"
    ls -lt "$BACKUP_DIR"/full_backup_*.tar.gz 2>/dev/null || echo "No backups found"
}

# Function to extract backup archive
extract_backup() {
    local backup_file=$1
    local extract_dir="$BACKUP_DIR/temp_restore"
    
    echo_message "Extracting backup archive..."
    mkdir -p "$extract_dir"
    tar -xzf "$backup_file" -C "$extract_dir"
    
    echo "$extract_dir"
}

# Function to restore database
restore_database() {
    local extract_dir=$1
    local db_backup=$(ls "$extract_dir"/db_backup_*.sql 2>/dev/null | head -n 1)
    
    if [ -f "$db_backup" ]; then
        echo_message "Restoring database..."
        # Drop and recreate database
        docker exec $DB_CONTAINER psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
        docker exec $DB_CONTAINER psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
        # Restore from backup
        cat "$db_backup" | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME
        echo_message "Database restored successfully"
    else
        echo_message "No database backup found to restore"
    fi
}

# Function to restore configuration
restore_config() {
    local extract_dir=$1
    local config_dir=$(ls -d "$extract_dir"/config_* 2>/dev/null | head -n 1)
    
    if [ -d "$config_dir" ]; then
        echo_message "Restoring configuration files..."
        
        # Restore .env file if it exists in backup
        if [ -f "$config_dir/.env" ]; then
            cp "$config_dir/.env" ./.env
            echo_message "Restored .env file"
        fi
        
        # Restore docker-compose.yml if it exists in backup
        if [ -f "$config_dir/docker-compose.yml" ]; then
            cp "$config_dir/docker-compose.yml" ./docker-compose.yml
            echo_message "Restored docker-compose.yml"
        fi
    else
        echo_message "No configuration backup found to restore"
    fi
}

# Function to restore models
restore_models() {
    local extract_dir=$1
    local models_dir=$(ls -d "$extract_dir"/models_* 2>/dev/null | head -n 1)
    
    if [ -d "$models_dir" ]; then
        echo_message "Restoring models..."
        mkdir -p backend/models
        cp -r "$models_dir"/* backend/models/
        echo_message "Models restored successfully"
    else
        echo_message "No models backup found to restore"
    fi
}

# Function to cleanup temporary files
cleanup() {
    local extract_dir="$BACKUP_DIR/temp_restore"
    if [ -d "$extract_dir" ]; then
        echo_message "Cleaning up temporary files..."
        rm -rf "$extract_dir"
    fi
}

# Main restore process
main() {
    if [ $# -eq 0 ]; then
        echo_message "Please provide a backup file to restore"
        list_backups
        exit 1
    fi
    
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        echo_message "Backup file not found: $backup_file"
        list_backups
        exit 1
    fi
    
    echo_message "Starting restore process..."
    
    # Extract backup
    local extract_dir=$(extract_backup "$backup_file")
    
    # Stop running containers
    echo_message "Stopping running containers..."
    docker compose down
    
    # Restore components
    restore_database "$extract_dir"
    restore_config "$extract_dir"
    restore_models "$extract_dir"
    
    # Cleanup
    cleanup
    
    # Restart containers
    echo_message "Restarting containers..."
    docker compose up -d
    
    echo_message "Restore process completed successfully!"
}

# Run main restore process
main "$@" 