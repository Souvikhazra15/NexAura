@echo off
cls
echo.
echo ====================================================
echo   AnomalySync - IoT Anomaly Detection System
echo   LAUNCHING BOTH BACKEND & FRONTEND
echo ====================================================
echo.
echo This will open TWO new terminals:
echo 1. Backend API (FastAPI) - Port 8000
echo 2. Frontend Dashboard (Next.js) - Port 3000
echo.
echo Starting...
echo.

REM Launch Backend in new terminal
start "AnomalySync Backend" cmd /k "cd backend && python main.py"

REM Wait 3 seconds for backend to start
timeout /t 3

REM Launch Frontend in new terminal
start "AnomalySync Frontend" cmd /k "cd frontend && npm install -q && npm run dev"

echo.
echo ====================================================
echo SERVERS STARTING - CHECK THE NEW WINDOWS
echo ====================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo API Docs: http://localhost:8000/docs
echo Dashboard will open shortly...
echo.
timeout /t 5
start http://localhost:3000
