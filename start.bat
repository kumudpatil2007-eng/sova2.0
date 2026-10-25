@echo off
title SOVA Launcher
echo ========================================================
echo   Starting SOVA (Air-Gapped Engineering Workbench)
echo ========================================================
echo.

:: 1. Check if Ollama is running, if not start it
echo [1/3] Checking Ollama daemon...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Starting Ollama in background...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo Ollama is already active.
)

:: 2. Start FastAPI Backend in new window
echo [2/3] Starting FastAPI Backend (:8000)...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "SOVA Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
) else (
    start "SOVA Backend" cmd /k "cd /d %~dp0backend && py -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

:: 3. Start Vite Frontend in new window
echo [3/3] Starting React Frontend (:5173)...
start "SOVA Frontend" cmd /k "cd /d %~dp0sovereign-ai && npm run dev"

:: 4. Wait briefly and open browser
echo.
echo SOVA is booting up! Opening browser...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================================
echo   Running at: http://localhost:5173
echo   (Keep the background terminal windows open while using)
echo ========================================================
