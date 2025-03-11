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
    }

    Write-Host "$Service not ready after $Retries retries. Continuing anyway..."
    return $false
}

# Set environment variables
$env:NODE_ENV = "development"
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"

# Wait for backend
Wait-ForService -HostName "localhost" -Port 8000 -Service "Backend service" -Retries 30 -Timeout 2

# Install dependencies if needed
if (-not (Test-Path "node_modules") -or -not (Test-Path "node_modules\.package-lock.json")) {
    Write-Host "Installing dependencies..."
    npm install
}
else {
    Write-Host "Dependencies are already installed"
}

# Build the application
Write-Host "Building the application..."
$buildResult = npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed, retrying once with clean install..."
    Remove-Item -Recurse -Force node_modules, .next -ErrorAction SilentlyContinue
    npm install
    npm run build
}

# Start the application
Write-Host "Starting the application..."
if ($env:NODE_ENV -eq "production") {
    npm run start
}
else {
    npm run dev
} 