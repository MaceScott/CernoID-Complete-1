@echo off
SETLOCAL EnableDelayedExpansion

:: Setup logging
SET LOG_DIR=logs
SET LOG_FILE=%LOG_DIR%\docker.log
IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

:: Check if Docker is installed
WHERE docker >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed >> %LOG_FILE%
    echo Docker is not installed
    exit /b 1
)

:: Check if Docker is running
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running >> %LOG_FILE%
    echo Docker is not running
    exit /b 1
)

:: Build and start containers
echo Starting Docker containers...
echo [%date% %time%] Starting Docker containers >> %LOG_FILE%
docker-compose up -d --build

:: Wait for containers to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak > nul

:: Check if containers are running
docker-compose ps | findstr "Up" > nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Containers failed to start >> %LOG_FILE%
    docker-compose logs >> %LOG_FILE%
    exit /b 1
)

echo Docker containers started successfully
echo [%date% %time%] Docker containers started successfully >> %LOG_FILE%

:: Open in browser
start http://localhost:3000 