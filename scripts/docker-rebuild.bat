@echo off
echo Cleaning and rebuilding Docker...

:: Stop all containers
echo Stopping all containers...
docker-compose down

:: Remove all related images
echo Removing old images...
docker rmi cernoid-app:latest
docker rmi $(docker images -q) -f

:: Clean Docker cache
echo Cleaning Docker cache...
docker builder prune -af
docker system prune -af --volumes

:: Rebuild from scratch
echo Rebuilding Docker containers...
docker-compose build --no-cache

:: Start the containers
echo Starting containers...
docker-compose up -d

:: Show logs
echo Showing logs...
docker-compose logs -f

echo Done!
pause 