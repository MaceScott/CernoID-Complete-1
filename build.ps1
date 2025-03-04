# Build script for CernoID

param(
    [Parameter()]
    [ValidateSet("frontend", "backend", "all")]
    [string]$Service = "all",
    
    [Parameter()]
    [switch]$NoPull,
    
    [Parameter()]
    [switch]$Clean
)

# Function to show progress
function Write-Step {
    param([string]$Message)
    Write-Host "`n🚀 $Message" -ForegroundColor Cyan
}

# Function to handle errors
function Handle-Error {
    param([string]$Message)
    Write-Host "`n❌ Error: $Message" -ForegroundColor Red
    exit 1
}

# Clean Docker resources if requested
if ($Clean) {
    Write-Step "Cleaning Docker resources..."
    docker compose down --volumes --remove-orphans
    docker system prune -f
}

# Pull images if not disabled
if (-not $NoPull) {
    Write-Step "Pulling latest base images..."
    if ($Service -eq "all" -or $Service -eq "frontend") {
        docker pull node:18-alpine
    }
    if ($Service -eq "all" -or $Service -eq "backend") {
        docker pull python:3.11-slim
    }
}

# Build services based on selection
try {
    if ($Service -eq "all" -or $Service -eq "frontend") {
        Write-Step "Building frontend..."
        docker compose build frontend
        if ($LASTEXITCODE -ne 0) { Handle-Error "Frontend build failed" }
    }

    if ($Service -eq "all" -or $Service -eq "backend") {
        Write-Step "Building backend..."
        docker compose build backend
        if ($LASTEXITCODE -ne 0) { Handle-Error "Backend build failed" }
    }

    Write-Step "Starting services..."
    if ($Service -eq "all") {
        docker compose up -d
    } else {
        docker compose up -d $Service
    }
    if ($LASTEXITCODE -ne 0) { Handle-Error "Failed to start services" }

    Write-Step "Build completed successfully! 🎉"
    Write-Host "`nServices are now running:"
    docker compose ps
} catch {
    Handle-Error $_.Exception.Message
} 