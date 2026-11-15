# QueueFlow — Start Backend (Windows PowerShell)
# Run from the project root: .\start-backend.ps1

$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir

# create venv if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    Write-Host "Installing dependencies..."
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
}

# copy .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit SECRET_KEY before production!"
}

Write-Host "Starting QueueFlow backend at http://localhost:8000"
Write-Host "API docs: http://localhost:8000/docs"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
