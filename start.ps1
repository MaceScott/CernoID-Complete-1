# Function to print colorful messages
function Write-Message {
    param([string]$Message)
    Write-Host "[CernoID] $Message" -ForegroundColor Blue
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

# Function to check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if a service is healthy
function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [int]$MaxAttempts = 20,
        [int]$SleepSeconds = 1
    )
    
    Write-Message "Waiting for $ServiceName to be healthy..."
    $attempts = 0
    while ($attempts -lt $MaxAttempts) {
        $health = docker inspect --format='{{.State.Health.Status}}' "cernoid-complete-1-$ServiceName-1" 2>$null
        if ($health -eq "healthy") {
            Write-Success "$ServiceName is healthy"
            return $true
        }
        $attempts++
        if ($attempts -lt $MaxAttempts) {
            Write-Message "Attempt $attempts/$MaxAttempts - $ServiceName not ready yet..."
            Start-Sleep -Seconds $SleepSeconds
        }
    }
    Write-Error "$ServiceName failed to become healthy after $MaxAttempts attempts"
    return $false
}

# Main startup sequence
function Start-CernoID {
    Write-Message "Starting CernoID System..."

    # Check if Docker is running
    if (-not (Test-Docker)) {
        Write-Error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    }

    # Start services
    Write-Message "Starting services..."
    docker-compose up -d

    # Wait for core services first
    if (-not (Test-ServiceHealth "db" -MaxAttempts 15 -SleepSeconds 1)) {
        exit 1
    }
    
    if (-not (Test-ServiceHealth "redis" -MaxAttempts 15 -SleepSeconds 1)) {
        exit 1
    }

    # Then wait for application services
    if (-not (Test-ServiceHealth "backend" -MaxAttempts 20 -SleepSeconds 1)) {
        exit 1
    }
    
    if (-not (Test-ServiceHealth "frontend" -MaxAttempts 20 -SleepSeconds 1)) {
        exit 1
    }

    # Get port numbers from environment or use defaults
    $frontendPort = if ($env:DOCKER_FRONTEND_PORT) { $env:DOCKER_FRONTEND_PORT } else { "3000" }
    
    # Open browser
    Write-Message "Opening browser..."
    Start-Process "http://localhost:$frontendPort"

    Write-Success "CernoID System is now running!"
    Write-Message "Press Ctrl+C to stop all services"

    # Keep the script running and handle shutdown gracefully
    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        Write-Message "Shutting down services..."
        docker-compose down
    }
}

# Start the system
Start-CernoID 