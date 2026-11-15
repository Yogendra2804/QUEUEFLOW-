# QueueFlow — Start Frontend (Windows PowerShell)
# Run from the project root: .\start-frontend.ps1

$frontendDir = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendDir

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "Starting QueueFlow frontend at http://localhost:5173"
npm run dev
