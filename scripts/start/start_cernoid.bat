@echo off
TITLE CernoID Security System
setlocal enabledelayedexpansion

:: Set up logging
set "LOGDIR=logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOGFILE=%LOGDIR%\cernoid.log"

:: Log function
call :LOG "Starting CernoID Security System"

:: Change to project directory
cd /d "C:\Users\maces\CernoID-Complete-1"
if errorlevel 1 (
    call :LOG "Error: Failed to change to project directory"
    echo Failed to locate CernoID directory.
    pause
    exit /b 1
)

:: Check Docker Desktop installation
if not exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    call :LOG "Error: Docker Desktop not found"
    echo Docker Desktop is not installed.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    start https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    call :LOG "Docker not running, attempting to start Docker Desktop"
    echo Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    :: Wait for Docker to start (max 60 seconds)
    set /a attempts=0
    :DOCKER_WAIT_LOOP
    timeout /t 2 >nul
    set /a attempts+=1
    docker info >nul 2>&1
    if errorlevel 1 (
        if !attempts! lss 30 (
            echo Waiting for Docker to start... Attempt !attempts!/30
            goto DOCKER_WAIT_LOOP
        ) else (
            call :LOG "Error: Docker failed to start after 60 seconds"
            echo Docker failed to start. Please start Docker Desktop manually.
            pause
            exit /b 1
        )
    )
)

:: Stop any running containers
call :LOG "Stopping any existing containers"
docker compose down >nul 2>&1

:: Start services
call :LOG "Starting CernoID services"
echo Starting CernoID services...
docker compose up -d
if errorlevel 1 (
    call :LOG "Error: Failed to start Docker services"
    echo Failed to start CernoID services.
    docker compose logs
    pause
    exit /b 1
)

:: Function to check specific service health
:CHECK_SERVICE
set "service=%~1"
docker compose ps %service% | findstr "healthy" >nul
exit /b

:: Wait for services to be healthy
echo Checking service health...
set /a health_checks=0
:HEALTH_CHECK_LOOP
timeout /t 2 >nul
set /a health_checks+=1

:: Check each service individually
call :CHECK_SERVICE backend
set backend_healthy=%errorlevel%
call :CHECK_SERVICE frontend
set frontend_healthy=%errorlevel%
call :CHECK_SERVICE db
set db_healthy=%errorlevel%

:: Display status
echo.
echo Service Status [Attempt !health_checks!/15]:
echo Backend: %backend_healthy% ^| Frontend: %frontend_healthy% ^| Database: %db_healthy%

:: Continue if all services are healthy
if %backend_healthy%==0 if %frontend_healthy%==0 if %db_healthy%==0 (
    goto SERVICES_READY
)

:: Retry if not exceeded max attempts
if !health_checks! lss 15 (
    goto HEALTH_CHECK_LOOP
) else (
    call :LOG "Error: Services failed health check"
    echo Services failed to start properly.
    echo.
    echo Detailed Status:
    docker compose ps
    echo.
    echo Service Logs:
    docker compose logs --tail=50
    pause
    exit /b 1
)

:SERVICES_READY
:: Verify API connectivity
echo Testing API connectivity...
curl -s http://localhost:8000/health >nul
if errorlevel 1 (
    call :LOG "Error: Backend API not responding"
    echo Backend API is not responding.
    echo Checking backend logs:
    docker compose logs backend --tail=50
    pause
    exit /b 1
)

:: Verify frontend is responding
echo Testing frontend accessibility...
curl -s http://localhost:3000 >nul
if errorlevel 1 (
    call :LOG "Error: Frontend not responding"
    echo Frontend is not responding.
    echo Checking frontend logs:
    docker compose logs frontend --tail=50
    pause
    exit /b 1
)

:: All services are running, open browser
call :LOG "All services started successfully"
echo.
echo CernoID is ready!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo.

:: Create desktop shortcut to this script
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut($WshShell.SpecialFolders('Desktop') + '\CernoID.lnk'); $Shortcut.TargetPath = '%~f0'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0\..\..\frontend\public\favicon.ico'; $Shortcut.Save()"

:: Open in default browser (directly to login)
timeout /t 2 >nul
start "" "http://localhost:3000/login"

:: Keep window open to show logs and allow clean shutdown
echo Press any key to shut down CernoID...
pause >nul

:: Clean shutdown
call :LOG "Shutting down CernoID"
echo Shutting down CernoID...
docker compose down
if errorlevel 1 (
    call :LOG "Warning: Clean shutdown failed"
    echo Warning: Some services may not have shut down properly.
)

echo.
echo CernoID has been shut down.
timeout /t 3 >nul
exit /b 0

:LOG
echo [%date% %time%] %~1 >> "%LOGFILE%"
exit /b 0 