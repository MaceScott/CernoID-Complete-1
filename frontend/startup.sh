#!/bin/bash

# Function to wait for a service with timeout and retries
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local retries=$4
    local timeout=$5
    local count=0

    echo "Waiting for $service to be ready..."
    while ! nc -z $host $port >/dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -gt $retries ]; then
            echo "$service not ready after $retries retries. Continuing anyway..."
            return 1
        fi
        echo "Attempt $count/$retries: $service is not ready - sleeping $timeout seconds"
        sleep $timeout
    done

    if [ $count -lt $retries ]; then
        echo "$service is ready"
        return 0
    fi
}

# Wait for backend with 30 retries, 2 seconds timeout
wait_for_service backend 8000 "Backend service" 30 2

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "Dependencies are already installed"
fi

# Build the application
echo "Building the application..."
if ! npm run build; then
    echo "Build failed, retrying once with clean install..."
    rm -rf node_modules .next
    npm install
    npm run build
fi

# Start the application
echo "Starting the application..."
if [ "$NODE_ENV" = "production" ]; then
    npm run start
else
    npm run dev
fi 