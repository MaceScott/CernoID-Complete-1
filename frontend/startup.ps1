# Function to wait for a service with timeout and retries
function Wait-ForService {
    param(
        [string]$HostName,
        [int]$Port,
        [string]$Service,
        [int]$Retries,
        [int]$Timeout
    )

    Write-Host "Waiting for $Service to be ready..."
    $count = 0

    while ($count -lt $Retries) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.ConnectAsync($HostName, $Port).Wait($Timeout * 1000) | Out-Null
            if ($tcp.Connected) {
                Write-Host "$Service is ready"
                $tcp.Close()
                return $true
            }
        }
        catch {
            $count++
            Write-Host "Attempt ${count}/${Retries}: $Service is not ready - waiting $Timeout seconds"
            Start-Sleep -Seconds $Timeout
        }
        finally {
            if ($tcp) {
                $tcp.Dispose()
            }
        }
    }

    Write-Host "$Service not ready after $Retries retries. Continuing anyway..."
    return $false
}

# Set environment variables
$env:NODE_ENV = "development"
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"

# Check if we're in the right directory
if (-not (Test-Path "package.json")) {
    Write-Host "Error: package.json not found. Make sure you're in the frontend directory."
    exit 1
}

# Install dependencies if needed
if (-not (Test-Path "node_modules") -or -not (Test-Path "package-lock.json")) {
    Write-Host "Installing dependencies..."
    try {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to install dependencies"
            exit 1
        }
    }
    catch {
        Write-Host "Error: Failed to install dependencies"
        Write-Host $_.Exception.Message
        exit 1
    }
}
else {
    Write-Host "Dependencies are already installed"
}

# Kill any existing processes on port 3000
try {
    $existingProcess = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    if ($existingProcess) {
        Stop-Process -Id $existingProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Killed existing process on port 3000"
    }
}
catch {
    Write-Host "Note: No existing process found on port 3000"
}

# Start the Next.js development server
Write-Host "Starting Next.js development server..."
$nextProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -NoNewWindow

# Wait for Next.js to be ready
Write-Host "Waiting for Next.js to start..."
$nextReady = Wait-ForService -HostName "localhost" -Port 3000 -Service "Next.js server" -Retries 15 -Timeout 2

if (-not $nextReady) {
    Write-Host "Error: Next.js server failed to start"
    if ($nextProcess -and !$nextProcess.HasExited) {
        Stop-Process -Id $nextProcess.Id -Force
    }
    exit 1
}

# Wait for backend
Write-Host "Checking backend service..."
$backendReady = Wait-ForService -HostName "localhost" -Port 8000 -Service "Backend service" -Retries 5 -Timeout 2

if (-not $backendReady) {
    Write-Host "Warning: Backend service not available. Some features may not work."
    Write-Host "Make sure the backend service is running on port 8000"
}

# Open the browser
Write-Host "Opening browser..."
Start-Process "http://localhost:3000/login"

# Keep the window open and show instructions
Write-Host "`nApplication is running!"
Write-Host "- Frontend: http://localhost:3000"
Write-Host "- Backend: http://localhost:8000"
Write-Host "`nPress Ctrl+C to stop the application"

try {
    Wait-Process -Id $nextProcess.Id
}
catch {
    Write-Host "`nApplication stopped."
}
finally {
    if ($nextProcess -and !$nextProcess.HasExited) {
        Stop-Process -Id $nextProcess.Id -Force
    }
} 