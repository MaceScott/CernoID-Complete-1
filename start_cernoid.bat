@echo off
cd /d "%~dp0"

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: Set Python path to include the src directory
set PYTHONPATH=%CD%

:: Create necessary directories if they don't exist
if not exist "config" mkdir config
if not exist "data\images" mkdir data\images
if not exist "logs" mkdir logs
if not exist "models" mkdir models

:: Run the application
python src/main.py

:: Keep the window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred while running the application.
    pause
)

:: Deactivate virtual environment
deactivate 