@echo off
echo Cleaning and rebuilding project...

:: Stop all running containers
echo Stopping running containers...
docker-compose down

:: Clean Docker cache
echo Cleaning Docker cache...
docker system prune -f

:: Remove build artifacts
echo Removing build artifacts...
if exist node_modules rmdir /s /q node_modules
if exist .next rmdir /s /q .next
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

:: Create virtual environment and install Python dependencies
echo Installing Python dependencies...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

:: Install Node.js dependencies
echo Installing Node.js dependencies...
npm install

:: Build the project
echo Building project...
npm run build

:: Start Docker containers
echo Starting Docker containers...
docker-compose up -d

echo Build complete!
pause 