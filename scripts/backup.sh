#!/bin/sh

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_HOST="db"
REDIS_HOST="redis"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Backup Redis
echo "Backing up Redis..."
redis-cli -h "$REDIS_HOST" -a "$REDIS_PASSWORD" SAVE
cp /data/dump.rdb "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# Compress backups
echo "Compressing backups..."
gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# Cleanup old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully!" 