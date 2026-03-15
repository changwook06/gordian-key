# Gordian Key Sidecar Build Script (PowerShell for Windows)

Write-Host "Starting build process for Gordian Key sidecar..." -ForegroundColor Cyan

# Navigate to the backend directory
Set-Location -Path $PSScriptRoot

# Create and activate virtual environment
python -m venv venv
& .\venv\Scripts\Activate.ps1

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Create output directory for Tauri sidecar
New-Item -ItemType Directory -Force -Path "..\src-tauri\sidecar"

# Run PyInstaller
# We bundle everything into a single binary named 'gordian_backend'
pyinstaller --onefile `
    --name gordian_backend `
    --distpath "..\src-tauri\sidecar" `
    --hidden-import ollama `
    --hidden-import cryptography `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols.http.auto `
    --collect-all ollama `
    main.py

Write-Host ""
Write-Host "-------------------------------------------------------" -ForegroundColor Green
Write-Host "Success! Sidecar binary built at: ..\src-tauri\sidecar\" -ForegroundColor Green
Write-Host "-------------------------------------------------------" -ForegroundColor Green

deactivate
