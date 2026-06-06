@echo off
title ARA AI Brain & OmniConvert Local Web Server
echo Starting ARA AI Brain Backend (port 8080)...
start /b python server.py
echo Starting OmniConvert Web Server (port 8000)...
python run_server.py
pause
