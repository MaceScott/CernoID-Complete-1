#!/bin/bash

# Backup script
set -e

# Setup
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

# Backup files
tar -czf "$BACKUP_FILE" \
    --exclude="node_modules" \
    --exclude=".next" \
    --exclude="$BACKUP_DIR" \
    .

echo "Backup created: $BACKUP_FILE" 