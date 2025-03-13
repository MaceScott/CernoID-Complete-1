@echo off
setlocal enabledelayedexpansion

:: Get both potential desktop paths
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v "Desktop"') do set "DESKTOP_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\OneDrive\Shell Folders" /v "Desktop" 2^>nul') do set "ONEDRIVE_DESKTOP_PATH=%%b"

:: Use OneDrive path if it exists
if defined ONEDRIVE_DESKTOP_PATH (
    set "DESKTOP_PATH=!ONEDRIVE_DESKTOP_PATH!"
)

:: Get the current directory (where CernoID is installed)
set "INSTALL_PATH=%~dp0"
set "INSTALL_PATH=%INSTALL_PATH:~0,-1%"

:: Verify required files exist
if not exist "%INSTALL_PATH%\start_cernoid.bat" (
    echo Error: start_cernoid.bat not found in %INSTALL_PATH%
    echo Please ensure you're running this script from the correct location.
    pause
    exit /b 1
)

if not exist "%INSTALL_PATH%\docker-compose.yml" (
    echo Error: docker-compose.yml not found in %INSTALL_PATH%
    echo Please ensure all required files are present.
    pause
    exit /b 1
)

:: Remove existing shortcut if it exists
if exist "%DESKTOP_PATH%\CernoID.lnk" (
    echo Removing existing shortcut...
    del "%DESKTOP_PATH%\CernoID.lnk"
)

:: Try multiple icon locations
set "ICON_PATH=%INSTALL_PATH%\frontend\public\favicon.ico"
if not exist "!ICON_PATH!" (
    set "ICON_PATH=%INSTALL_PATH%\frontend\public\images\logo.ico"
    if not exist "!ICON_PATH!" (
        set "ICON_PATH=%INSTALL_PATH%\assets\images\logo.ico"
        if not exist "!ICON_PATH!" (
            :: Use Docker Desktop icon as fallback
            set "ICON_PATH=%ProgramFiles%\Docker\Docker\Docker Desktop.exe,0"
        )
    )
)

:: Create VBScript to make the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP_PATH%\CernoID.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%INSTALL_PATH%\start_cernoid.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%ICON_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "CernoID Security System" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

:: Create the shortcut
cscript //nologo "%TEMP%\CreateShortcut.vbs"

:: Clean up
del "%TEMP%\CreateShortcut.vbs"

:: Verify creation
if exist "%DESKTOP_PATH%\CernoID.lnk" (
    echo.
    echo Desktop shortcut created successfully!
    echo Location: %DESKTOP_PATH%\CernoID.lnk
    echo Working Directory: %INSTALL_PATH%
    echo Target: start_cernoid.bat
    echo Icon: %ICON_PATH%
    echo.
) else (
    echo.
    echo Failed to create desktop shortcut
    echo Attempted path: %DESKTOP_PATH%\CernoID.lnk
    echo Please check permissions and try again.
    echo.
)

pause 