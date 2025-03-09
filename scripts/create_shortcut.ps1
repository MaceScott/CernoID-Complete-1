# Get the actual desktop path
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "CernoID.lnk"
$TargetPath = Join-Path $PSScriptRoot "start\Start_CernoID.bat"
$WorkingDirectory = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

# Ensure the target batch file exists
if (-not (Test-Path $TargetPath)) {
    Write-Host "Error: Could not find Start_CernoID.bat at $TargetPath"
    exit 1
}

# Try multiple icon locations
$IconPath = Join-Path $WorkingDirectory "frontend\public\favicon.ico"
if (-not (Test-Path $IconPath)) {
    $IconPath = Join-Path $WorkingDirectory "frontend\public\icon.ico"
}
if (-not (Test-Path $IconPath)) {
    $IconPath = Join-Path $WorkingDirectory "frontend\src\assets\icon.ico"
}

# Create WScript Shell Object
$WScriptShell = New-Object -ComObject WScript.Shell

# Remove existing shortcut if it exists
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
}

# Create the shortcut
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDirectory
$Shortcut.Description = "Launch CernoID Security System"
$Shortcut.WindowStyle = 1  # Normal window

# Set icon - try custom icon first, then Docker icon, then default
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
    Write-Host "Using custom icon from: $IconPath"
} else {
    $DockerIconPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $DockerIconPath) {
        $Shortcut.IconLocation = "$DockerIconPath,0"
        Write-Host "Using Docker Desktop icon as fallback"
    } else {
        Write-Host "Using default icon"
    }
}

# Save the shortcut
$Shortcut.Save()

# Make the shortcut run as administrator
$bytes = [System.IO.File]::ReadAllBytes($ShortcutPath)
$bytes[0x15] = $bytes[0x15] -bor 0x20 #set byte 21 (0x15) bit 6 (0x20) ON
[System.IO.File]::WriteAllBytes($ShortcutPath, $bytes)

# Create startup shortcut (optional)
$StartupPath = [Environment]::GetFolderPath('Startup')
$StartupShortcut = Join-Path $StartupPath "CernoID.lnk"
if (Test-Path $StartupShortcut) {
    Remove-Item $StartupShortcut -Force
}
Copy-Item -Path $ShortcutPath -Destination $StartupShortcut -Force

# Verify shortcut creation
if (Test-Path $ShortcutPath) {
    Write-Host "`nShortcuts created successfully!"
    Write-Host "Desktop shortcut: $ShortcutPath"
    Write-Host "Startup shortcut: $StartupShortcut"
    Write-Host "`nImportant Notes:"
    Write-Host "1. The shortcut will automatically start Docker if needed"
    Write-Host "2. Services will be health-checked before launching"
    Write-Host "3. The application will open directly to the login page"
    Write-Host "4. Press any key in the command window to shut down properly"
} else {
    Write-Host "Error: Failed to create shortcuts"
    exit 1
} 