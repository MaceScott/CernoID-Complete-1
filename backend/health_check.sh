#!/bin/bash
set -e

# Check if the application is responding
curl -f http://localhost:8000/health || exit 1

# Check if PostgreSQL is accessible
PGPASSWORD=$DB_PASSWORD psql -h "db" -U "$DB_USER" -d "$DB_NAME" -c '\q' || exit 1

# Check if Redis is accessible
redis-cli -h redis ping || exit 1 