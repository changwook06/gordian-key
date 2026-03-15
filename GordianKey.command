#!/bin/bash
# Gordian Key Launcher
# This script starts the backend and opens the desktop window.

# Move to the project root directory
cd "$(dirname "$0")"

echo "-------------------------------------------------------"
echo "🚀 GORDIAN KEY IS STARTING..."
echo "-------------------------------------------------------"

# 1. Start the Python Backend in the background
echo "Starting Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "First time setup: Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run backend on port 52731 (as configured in the app)
python main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 2. Start the Frontend/Tauri Desktop Window
echo "Starting Desktop Interface..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "First time setup: Installing Node.js dependencies..."
    npm install
fi

# This opens the actual Gordian Key window
# Tauri v2 expects to be run from the directory containing src-tauri/tauri.conf.json
cd ..
npm --prefix frontend run tauri dev

# 3. Cleanup: Kill the backend when the window is closed
echo "Shutting down Gordian Key..."
kill $BACKEND_PID
echo "Done."
