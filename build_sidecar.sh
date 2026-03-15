#!/bin/bash
# Gordian Key Sidecar Build Script (POSIX-compliant)

set -e

echo "Starting build process for Gordian Key sidecar..."

# Navigate to the backend directory (where the script is located)
cd "$(dirname "$0")"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Create output directory for Tauri sidecar
mkdir -p ../src-tauri/sidecar

# Run PyInstaller
# We bundle everything into a single binary named 'gordian_backend'
pyinstaller --onefile \
    --name gordian_backend \
    --distpath ../src-tauri/sidecar \
    --hidden-import ollama \
    --hidden-import cryptography \
    --hidden-import uvicorn.logging \
    --hidden-import uvicorn.loops.auto \
    --hidden-import uvicorn.protocols.http.auto \
    --collect-all ollama \
    main.py

echo ""
echo "-------------------------------------------------------"
echo "Success! Sidecar binary built at: ../src-tauri/sidecar/"
echo "-------------------------------------------------------"

deactivate
