#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to print messages
echo_message() {
    echo "[INSTALL] $1"
}

# Update package list and install dependencies
echo_message "Updating package list and installing dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
    postgresql \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up PostgreSQL
echo_message "Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER cernoid WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE cernoid_db OWNER cernoid;"

# Apply database migrations
echo_message "Applying database migrations..."
# Assuming a migration tool like Alembic is used
# alembic upgrade head

# Set environment variables
echo_message "Setting environment variables..."
export DATABASE_URL="postgresql://cernoid:password@localhost/cernoid_db"

# Install Python dependencies
echo_message "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Build frontend assets
echo_message "Building frontend assets..."
npm run build

# Start the application
echo_message "Starting the application..."
# Assuming a command to start the application, e.g.,
# python src/main.py

# Print completion message
echo_message "Installation and setup complete!" 