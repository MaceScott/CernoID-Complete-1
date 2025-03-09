@echo off
TITLE CernoID Security System
setlocal enabledelayedexpansion

:: Set up logging
set "LOGDIR=logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOGFILE=%LOGDIR%\cernoid.log"

:: Load environment variables
if exist ".env" (
    for /F "tokens=*" %%i in (.env) do (
        set %%i
    )
)

:: Determine environment and set URLs
if "%NODE_ENV%"=="production" (
    set "FRONTEND_URL=%PROD_FRONTEND_URL%"
    set "BACKEND_URL=%PROD_BACKEND_URL%"
) else (
    set "FRONTEND_URL=%DEV_FRONTEND_URL%"
    set "BACKEND_URL=%DEV_BACKEND_URL%"
)

:: Log startup
call :LOG "Starting CernoID Security System in %NODE_ENV% mode"
echo Starting CernoID in %NODE_ENV% mode...

:: Change to project directory
cd /d "%~dp0..\.."
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
curl -s "%BACKEND_URL%/health" >nul
if errorlevel 1 (
    call :LOG "Error: Backend API not responding at %BACKEND_URL%"
    echo Backend API is not responding.
    echo Checking backend logs:
    docker compose logs backend --tail=50
    pause
    exit /b 1
)

:: Verify frontend is responding
echo Testing frontend accessibility...
curl -s "%FRONTEND_URL%" >nul
if errorlevel 1 (
    call :LOG "Error: Frontend not responding at %FRONTEND_URL%"
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
echo Frontend: %FRONTEND_URL%
echo Backend API: %BACKEND_URL%
echo Environment: %NODE_ENV%
echo.

:: Wait longer for services to be fully ready and verify they're responding
echo Waiting for services to be fully initialized...
timeout /t 10 /nobreak >nul

:: Double check frontend is responding
echo Verifying frontend access...
curl -v "%FRONTEND_URL%/login" >nul 2>&1
if errorlevel 1 (
    echo Frontend is not responding. Checking logs...
    docker compose logs frontend --tail=50
    pause
    exit /b 1
)

:: Open in default browser (directly to login)
echo Opening CernoID in your browser...
start "" "%FRONTEND_URL%/login"

:: Keep window open with status display
echo.
echo ========================================
echo CernoID Status
echo ========================================
echo.
echo Services are running! Do not close this window.
echo The application will remain active as long as
echo this window stays open.
echo.
echo To access CernoID:
echo   Login page: %FRONTEND_URL%/login
echo   API: %BACKEND_URL%
echo   Environment: %NODE_ENV%
echo.
echo To stop CernoID, close this window.
echo ========================================

:: Show running containers
echo.
echo Current running services:
docker compose ps
echo.

:: Keep the window open
pause
exit /b 0

:LOG
echo [%date% %time%] %~1 >> "%LOGFILE%"
exit /b 0 