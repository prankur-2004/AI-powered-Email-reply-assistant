@echo off
title AI-Powered Email Reply Assistant Launcher
echo ========================================================
echo  AI-POWERED EMAIL REPLY ASSISTANT
echo  Permanent URL: http://localhost:5173
echo ========================================================
echo.

set "PROJ_DIR=%~dp0"
set "PROJ_DIR=%PROJ_DIR:~0,-1%"

echo [1/3] Starting Local AI Server (Port 8001)...
start "Local AI Server (Port 8001)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='Local AI Server (8001)'; Set-Location '%PROJ_DIR%\backend'; & '..\.venv\Scripts\python.exe' -u custom_ai_server.py --port 8001"

echo [2/3] Starting Django Backend (Port 8000)...
start "Django Backend (Port 8000)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='Django Backend (8000)'; Set-Location '%PROJ_DIR%\backend'; & '..\.venv\Scripts\python.exe' manage.py runserver --noreload 127.0.0.1:8000"

echo [3/3] Starting React Frontend (Port 5173)...
start "React Frontend (Port 5173)" powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='React Frontend (5173)'; Set-Location '%PROJ_DIR%\frontend'; npm run dev"

echo.
echo ========================================================
echo  All services are launching!
echo  Opening http://localhost:5173 in your default browser...
echo ========================================================
echo.

ping 127.0.0.1 -n 3 >nul
start http://localhost:5173
