@echo off
setlocal enabledelayedexpansion

:: Check for running containers
echo Checking for running containers...
for /f "tokens=*" %%i in ('docker ps -q -f "name=cernoid-*"') do (
    echo Stopping container: %%i
    docker stop %%i
)

:: Clean up old containers and images
echo Cleaning up old containers and images...
docker-compose down --remove-orphans
docker system prune -f

:: Rebuild everything
echo Rebuilding project...
call npm ci
call pip install -r requirements.txt
call pip install -r requirements-dev.txt

:: Run tests
echo Running tests...
call npm run test
call pytest

:: Build and start containers
echo Starting services...
docker-compose up --build -d

echo Done! Services are starting up... 