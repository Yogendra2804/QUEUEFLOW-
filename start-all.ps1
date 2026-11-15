# QueueFlow — Start Both Backend and Frontend in separate windows (Windows PowerShell)
# Run from project root: .\start-all.ps1

$root = $PSScriptRoot

Write-Host "Starting QueueFlow Backend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\start-backend.ps1"

Write-Host "Starting QueueFlow Frontend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\start-frontend.ps1"

Write-Host "Both services are starting!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend API: http://localhost:8000"
Write-Host "API Docs: http://localhost:8000/docs"
