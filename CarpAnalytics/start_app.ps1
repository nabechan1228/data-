# CarpAnalytics Startup Script (PowerShell)

Write-Host "--- Starting CarpAnalytics Launch Process ---" -ForegroundColor Cyan

# 1. Cleanup old processes
Write-Host "[1/3] Cleaning up existing processes..." -ForegroundColor Yellow
$ports = @(8001, 5173)
foreach ($port in $ports) {
    try {
        $procId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
        if ($procId) {
            Write-Host "Stopping process $procId using port $port."
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Ignore errors
    }
}

# 2. Start Servers
Write-Host "[2/3] Starting servers..." -ForegroundColor Yellow

# Start Backend
$backendPath = Join-Path $PSScriptRoot "backend"
$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; & '$venvPython' main.py" -WindowStyle Normal
Write-Host "  -> Backend started in a new window (Port: 8001)"

# Start Frontend
$frontendPath = Join-Path $PSScriptRoot "frontend"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev" -WindowStyle Normal
Write-Host "  -> Frontend started in a new window (Port: 5173)"

# 3. Open Browser
Write-Host "[3/3] Preparing browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 5 # Wait for startup
Start-Process "http://127.0.0.1:5173"
Write-Host "--- Ready! Please check your browser ---" -ForegroundColor Green
