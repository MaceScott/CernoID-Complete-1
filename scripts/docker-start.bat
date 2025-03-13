@echo off
cd %~dp0\..
echo Starting CernoID Security System...
docker-compose up -d
echo Opening CernoID in your default browser...
timeout /t 5
start http://localhost:3000
echo CernoID Security System is running.
echo Press any key to close this window...
pause > nul 