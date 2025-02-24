#!/bin/sh

# Activate virtual environment
. /app/venv/bin/activate

# Start Python backend
python3 main.py &

# Start Next.js frontend
node server.js 