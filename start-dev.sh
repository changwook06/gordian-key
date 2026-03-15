#!/bin/bash

# Gordian Key — Development Mode
# Backend:  http://127.0.0.1:52731
# Frontend: http://localhost:1420
#
# Open http://localhost:1420 in your browser to use the app.
# Press Ctrl+C to stop both servers.

# Function to cleanup background processes
cleanup() {
    echo "Stopping Gordian Key servers..."
    if [ -f /tmp/gordian_backend.pid ]; then
        PID=$(cat /tmp/gordian_backend.pid)
        kill $PID 2>/dev/null
        rm /tmp/gordian_backend.pid
    fi
    exit
}

# Register cleanup on Ctrl+C (SIGINT)
trap cleanup SIGINT

echo "Gordian Key — Development Mode"
echo "Backend:  http://127.0.0.1:52731"
echo "Frontend: http://localhost:1420"
echo ""
echo "Open http://localhost:1420 in your browser to use the app."
echo "Press Ctrl+C to stop both servers."
echo ""

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# 2. Check Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed."
    exit 1
fi

# 3. Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it from https://ollama.com"
    exit 1
fi

# 4. Check if Ollama is running
if ! curl -s http://localhost:11434 &> /dev/null; then
    echo "Ollama is not running. Please start the Ollama application."
    exit 1
fi

# 5. Check mistral model
if ! ollama list | grep -q "mistral"; then
    echo "Mistral model not found. Pulling mistral..."
    ollama pull mistral
fi

# 6. Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# 7. Check Python dependencies
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -r backend/requirements.txt
fi

# 8. Start Python Backend in background
echo "Starting backend..."
python3 backend/main.py > /tmp/gordian_backend.log 2>&1 &
echo $! > /tmp/gordian_backend.pid

# 9. Wait 2 seconds and check health
sleep 2
if ! curl -s http://127.0.0.1:52731/health | grep -q "ok"; then
    echo "Error: Backend failed to start correctly."
    cleanup
    exit 1
fi

# 10. Start Vite Dev Server in foreground
echo "Starting frontend..."
cd frontend && npm run dev
