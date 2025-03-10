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

    # Wait a few seconds for services to initialize
    Start-Sleep -Seconds 5

    # Get port numbers from environment or use defaults
    $frontendPort = if ($env:DOCKER_FRONTEND_PORT) { $env:DOCKER_FRONTEND_PORT } else { "3000" }
    
    # Open browser
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