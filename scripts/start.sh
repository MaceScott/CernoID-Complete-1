#!/bin/bash

# Enable error handling
set -e

# Setup logging
LOG_DIR="$(dirname "$0")/../logs"
LOG_FILE="$LOG_DIR/startup.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

error() {
    log "ERROR: $1"
    exit 1
}

# Navigate to application directory
cd "$(dirname "$0")/.."
log "Working directory: $(pwd)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    error "Node.js is not installed. Please install Node.js first."
fi

# Log Node.js version
log "Node version: $(node -v)"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    error "package.json not found. Are you in the correct directory?"
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    log "Installing dependencies..."
    if ! npm install >> "$LOG_FILE" 2>&1; then
        error "Failed to install dependencies"
    fi
fi

# Build the application if needed
if [ ! -d ".next" ]; then
    log "Building application..."
    if ! npm run build >> "$LOG_FILE" 2>&1; then
        error "Build failed"
    fi
fi

# Check if port 3000 is available
if lsof -i:3000 > /dev/null 2>&1; then
    log "WARNING: Port 3000 is already in use"
    read -p "Do you want to kill the process using port 3000? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:3000 | xargs kill -9
        sleep 2
    else
        exit 1
    fi
fi

# Start the application
log "Starting Cernoid Security System..."
npm run start >> "$LOG_FILE" 2>&1 &
APP_PID=$!

# Wait and check if the application started successfully
sleep 5
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    error "Application failed to start"
fi

# Open in default browser
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v gnome-open > /dev/null; then
    gnome-open http://localhost:3000
elif command -v kde-open > /dev/null; then
    kde-open http://localhost:3000
fi

log "Application started successfully"
echo "Check $LOG_FILE for detailed logs"
echo "Press Ctrl+C to stop the application"

# Cleanup on exit
trap 'kill $APP_PID' EXIT
wait $APP_PID 