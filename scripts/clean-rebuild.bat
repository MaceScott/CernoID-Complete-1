@echo off
echo Cleaning and rebuilding...

:: Stop all containers
docker-compose down

:: Clean Docker cache
docker builder prune -af
docker system prune -af --volumes

:: Remove local build artifacts
if exist .next rmdir /s /q .next
if exist node_modules rmdir /s /q node_modules

:: Clean install dependencies
npm clean-install

:: Rebuild Docker
docker-compose build --no-cache

:: Start services
docker-compose up -d

echo Done!
pause 