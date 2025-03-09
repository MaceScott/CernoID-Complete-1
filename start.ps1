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
        [string]$Service,
        [int]$MaxAttempts
    )
    
    Write-Message "Waiting for $Service to be healthy..."
    $attempt = 1
    
    while ($attempt -le $MaxAttempts) {
        $status = docker-compose ps $Service | Select-String "healthy"
        if ($status) {
            Write-Success "$Service is healthy!"
            return $true
        }
        Write-Message ("Attempt {0}/{1}: {2} is not ready yet..." -f $attempt, $MaxAttempts, $Service)
        Start-Sleep -Seconds 5
        $attempt++
    }
    
    Write-Error "$Service failed to become healthy after $MaxAttempts attempts"
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

    # Create necessary directories
    New-Item -ItemType Directory -Force -Path logs, data/images, data/temp, models | Out-Null

    # Ensure .env file exists
    if (-not (Test-Path .env)) {
        if (Test-Path .env.example) {
            Write-Message "Creating .env file from .env.example..."
            Copy-Item .env.example .env
        }
        else {
            Write-Error ".env file not found and no .env.example to copy from"
            exit 1
        }
    }

    # Pull latest images and build services
    Write-Message "Building and starting services..."
    docker-compose pull
    docker-compose build --no-cache

    # Start services
    docker-compose up -d

    # Check service health
    $services = @("db", "redis", "backend", "frontend")
    foreach ($service in $services) {
        if (-not (Test-ServiceHealth -Service $service -MaxAttempts 12)) {
            Write-Error "Failed to start $service. Check logs with: docker-compose logs $service"
            docker-compose down
            exit 1
        }
    }

    # Get port numbers from environment or use defaults
    $frontendPort = if ($env:DOCKER_FRONTEND_PORT) { $env:DOCKER_FRONTEND_PORT } else { "3000" }
    $backendPort = if ($env:DOCKER_BACKEND_PORT) { $env:DOCKER_BACKEND_PORT } else { "8000" }

    Write-Success "CernoID System is now running!"
    Write-Message ("Access the application at: http://localhost:{0}" -f $frontendPort)
    Write-Message ("API documentation at: http://localhost:{0}/docs" -f $backendPort)
    Write-Message "Use Ctrl+C to stop all services"

    # Keep the script running and handle shutdown gracefully
    try {
        Get-Content -Path logs/app.log -Wait
    }
    finally {
        Write-Message "Shutting down services..."
        docker-compose down
    }
}

# Start the system
Start-CernoID 