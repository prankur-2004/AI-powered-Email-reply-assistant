# AI-Powered Email Reply Assistant - PowerShell Launcher
$projectRoot = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       AI-POWERED EMAIL REPLY ASSISTANT                 " -ForegroundColor Green
Write-Host "       Permanent URL: http://localhost:5173             " -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Start Local AI Server
Write-Host "[1/3] Starting Local AI Server (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Local AI Server (8001)'; Set-Location '$projectRoot\backend'; & '..\.venv\Scripts\python.exe' -u custom_ai_server.py --port 8001"

# 2. Start Django Backend
Write-Host "[2/3] Starting Django Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Django Backend (8000)'; Set-Location '$projectRoot\backend'; & '..\.venv\Scripts\python.exe' manage.py runserver --noreload 127.0.0.1:8000"

# 3. Start React Frontend
Write-Host "[3/3] Starting React Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='React Frontend (5173)'; Set-Location '$projectRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "  - Frontend:    http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API: http://127.0.0.1:8000/api/auth/" -ForegroundColor White
Write-Host "  - AI Server:   http://127.0.0.1:8001/" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
