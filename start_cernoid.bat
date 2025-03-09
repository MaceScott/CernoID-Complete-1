@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://www.python.org/
    pause
    exit /b 1
)

:: Create and activate virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install requirements if needed
pip list | findstr "fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements
        pause
        exit /b 1
    )
)

:: Set environment variables
set PYTHONPATH=%CD%\backend;%CD%\backend\src
set DEBUG=true
set ENVIRONMENT=development
set PYTHONUNBUFFERED=1

:: Database configuration
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=cernoid
set DB_USER=postgres
set DB_PASSWORD=postgres
set DB_POOL_MIN_SIZE=1
set DB_POOL_MAX_SIZE=5
set DB_TIMEOUT=30

:: Create necessary directories
echo Creating necessary directories...
mkdir "backend\src\core\face_recognition\data" 2>nul
mkdir "config" 2>nul
mkdir "data\images" 2>nul
mkdir "logs" 2>nul
mkdir "models" 2>nul

:: Create default config if it doesn't exist
if not exist "config\config.json" (
    echo Creating default configuration...
    echo { > config\config.json
    echo   "database": { >> config\config.json
    echo     "host": "localhost", >> config\config.json
    echo     "port": 5432, >> config\config.json
    echo     "name": "cernoid", >> config\config.json
    echo     "user": "postgres", >> config\config.json
    echo     "password": "postgres" >> config\config.json
    echo   }, >> config\config.json
    echo   "face_recognition": { >> config\config.json
    echo     "min_face_size": 64, >> config\config.json
    echo     "matching_threshold": 0.6, >> config\config.json
    echo     "cache_size": 1000, >> config\config.json
    echo     "cache_ttl": 3600 >> config\config.json
    echo   } >> config\config.json
    echo } >> config\config.json
)

:: Check if main.py exists
if not exist "backend\src\main.py" (
    echo Error: main.py not found in backend\src directory
    echo Current directory: %CD%
    echo Please ensure the application files are in the correct location
    pause
    exit /b 1
)

:: Run the application
echo Starting CernoID application...
cd backend\src
if not exist "logs" mkdir "logs" 2>nul

:: Clear previous log files
if exist "logs\error.log" del /f "logs\error.log"
if exist "logs\output.log" del /f "logs\output.log"

echo Starting application in development mode...
python main.py > logs\output.log 2>logs\error.log
set EXIT_CODE=!errorlevel!
cd ..\..

:: Handle errors
if !EXIT_CODE! neq 0 (
    echo.
    echo An error occurred while running the application.
    echo --- Error Log ---
    type backend\src\logs\error.log
    echo.
    echo --- Output Log ---
    type backend\src\logs\output.log
    echo.
    echo Please ensure PostgreSQL is installed and running on localhost:5432
    echo with the following credentials:
    echo   Database: cernoid
    echo   Username: postgres
    echo   Password: postgres
    echo.
    echo You can modify these settings in config\config.json
    pause
)

:: Deactivate virtual environment
deactivate
endlocal 