# Create necessary directories
New-Item -ItemType Directory -Force -Path "src/lib/hooks"
New-Item -ItemType Directory -Force -Path "src/lib/utils"

# Move hooks to the correct location
if (Test-Path "src/frontend/src/hooks") {
    Move-Item -Force "src/frontend/src/hooks/*" "src/lib/hooks/" -ErrorAction SilentlyContinue
}

# Move utils to the correct location
if (Test-Path "src/frontend/src/utils") {
    Move-Item -Force "src/frontend/src/utils/*" "src/lib/utils/" -ErrorAction SilentlyContinue
}

# Ensure utils.ts is in the correct location
if (Test-Path "src/lib/utils/utils.ts") {
    Move-Item -Force "src/lib/utils/utils.ts" "src/lib/utils/index.ts" -ErrorAction SilentlyContinue
}

# Clean up empty directories
if (Test-Path "src/frontend/src/hooks") {
    Remove-Item -Force -Recurse "src/frontend/src/hooks" -ErrorAction SilentlyContinue
}
if (Test-Path "src/frontend/src/utils") {
    Remove-Item -Force -Recurse "src/frontend/src/utils" -ErrorAction SilentlyContinue
}

Write-Host "Frontend files organized successfully" 