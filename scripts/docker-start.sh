#!/bin/bash

# Setup logging
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/docker.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log "ERROR: Docker is not installed"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    log "ERROR: Docker is not running"
    exit 1
fi

# Build and start containers
log "Starting Docker containers..."
docker-compose up -d --build

# Wait for containers to be ready
log "Waiting for services to be ready..."
sleep 10

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    log "ERROR: Containers failed to start"
    docker-compose logs >> "$LOG_FILE"
    exit 1
fi

log "Docker containers started successfully"

# Open in browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:3000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:3000
else
    start http://localhost:3000
fi 