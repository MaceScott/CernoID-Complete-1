@echo off
TITLE Cernoid Security System

:: Enable error logging
SET LOG_FILE=%~dp0..\logs\startup.log
IF NOT EXIST "%~dp0..\logs" MKDIR "%~dp0..\logs"

echo [%date% %time%] Starting Cernoid Security System >> %LOG_FILE%

:: Check if Node.js is installed
where node >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js first.
    echo [%date% %time%] ERROR: Node.js not found >> %LOG_FILE%
    pause
    exit /b 1
)

:: Log Node.js version
echo [%date% %time%] Node version: >> %LOG_FILE%
node -v >> %LOG_FILE%

:: Navigate to application directory
cd %~dp0..
echo [%date% %time%] Working directory: %cd% >> %LOG_FILE%

:: Check if package.json exists
IF NOT EXIST "package.json" (
    echo [ERROR] package.json not found. Are you in the correct directory?
    echo [%date% %time%] ERROR: package.json not found >> %LOG_FILE%
    pause
    exit /b 1
)

:: Install dependencies if needed
IF NOT EXIST "node_modules" (
    echo Installing dependencies...
    echo [%date% %time%] Installing dependencies >> %LOG_FILE%
    npm install >> %LOG_FILE% 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies
        echo [%date% %time%] ERROR: npm install failed >> %LOG_FILE%
        pause
        exit /b 1
    )
)

:: Build the application if needed
IF NOT EXIST ".next" (
    echo Building application...
    echo [%date% %time%] Building application >> %LOG_FILE%
    npm run build >> %LOG_FILE% 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Build failed
        echo [%date% %time%] ERROR: Build failed >> %LOG_FILE%
        pause
        exit /b 1
    )
)

:: Check if port 3000 is available
netstat -ano | findstr :3000 > nul
IF %ERRORLEVEL% EQU 0 (
    echo [WARNING] Port 3000 is already in use
    echo [%date% %time%] WARNING: Port 3000 already in use >> %LOG_FILE%
    choice /M "Do you want to kill the process using port 3000"
    IF %ERRORLEVEL% EQU 1 (
        FOR /F "tokens=5" %%P IN ('netstat -ano ^| findstr :3000') DO taskkill /F /PID %%P
        timeout /t 2
    ) ELSE (
        exit /b 1
    )
)

:: Start the application
echo Starting Cernoid Security System...
echo [%date% %time%] Starting application >> %LOG_FILE%
start /B npm run start >> %LOG_FILE% 2>&1

:: Wait and check if the application started successfully
timeout /t 5
curl -f http://localhost:3000 >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Application failed to start
    echo [%date% %time%] ERROR: Application failed to start >> %LOG_FILE%
    pause
    exit /b 1
)

:: Open in default browser
start http://localhost:3000
echo [%date% %time%] Application started successfully >> %LOG_FILE%

echo Cernoid Security System is running!
echo Check %LOG_FILE% for detailed logs
echo Press Ctrl+C to stop the application 