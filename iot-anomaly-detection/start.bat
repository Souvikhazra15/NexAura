@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Anomaly Detection System - Startup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.9+ is required but not found
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js 18+ is required but not found
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Checking prerequisites...
echo OK: Python and Node.js found
echo.

:: Setup Backend
echo [2/4] Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo OK: Backend dependencies installed
echo.

:: Start Backend
echo [3/4] Starting backend server...
echo Starting on http://localhost:8000
start "Backend Server" cmd /k python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak

:: Setup Frontend
echo [4/4] Setting up frontend...
cd ..\frontend

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

echo OK: Frontend dependencies installed
echo.

:: Start Frontend
echo ============================================
echo   System Starting...
echo ============================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C in the terminal windows to stop
echo.

call npm run dev

pause
