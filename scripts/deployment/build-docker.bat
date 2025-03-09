@echo off
echo Building Docker containers...

:: Set BuildKit environment variable for Windows
set "DOCKER_BUILDKIT=1"

:: Remove existing containers and images
docker-compose down
docker system prune -f

:: Build with increased memory
docker-compose build --no-cache --memory=4g

echo Build complete!
pause 