#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting CernoID Security System..."
docker-compose up -d
echo "Opening CernoID in your default browser..."
sleep 5
xdg-open http://localhost:3000
echo "CernoID Security System is running."
echo "Press Enter to close this window..."
read 