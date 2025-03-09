#!/bin/bash

# Deployment script
set -e

# Setup logging
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/deploy.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check environment file
if [ ! -f ".env" ]; then
    log "ERROR: .env file not found"
    log "Creating from example..."
    cp .env.example .env
    log "Please update .env with your configuration"
    exit 1
fi

# Install dependencies
log "Installing dependencies..."
npm install

# Build application
log "Building application..."
npm run build

# Create desktop shortcut
log "Creating desktop shortcut..."
npm run create-shortcut

log "Deployment complete!"
log "You can now start the application using the desktop shortcut"

# Build and push Docker image
docker build -t surveillance-system .
docker tag surveillance-system:latest your-registry/surveillance-system:latest
docker push your-registry/surveillance-system:latest

# Update Kubernetes deployment
kubectl apply -f k8s/
kubectl rollout restart deployment surveillance-system 