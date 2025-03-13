@echo off
cd /d "%~dp0"

:: Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

:: Start the application
echo Starting CernoID...
docker-compose up -d

:: Wait for services to be ready (max 10 seconds)
echo Waiting for services...
for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    curl -sf http://localhost:3000/api/health >nul 2>&1
    if not errorlevel 1 (
        goto :start_browser
    )
)

:start_browser
:: Open browser to login page
start http://localhost:3000/login

echo CernoID is running!
echo - Frontend: http://localhost:3000
echo - Backend: http://localhost:8000
echo.
echo To stop the application, run: docker-compose down
exit /b 0 