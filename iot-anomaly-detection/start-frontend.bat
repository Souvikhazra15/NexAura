@echo off
cls
echo.
echo ============================================
echo  AnomalySync Frontend Dashboard
echo ============================================
echo.
cd /d "%~dp0frontend"

echo Installing dependencies...
call npm install -q

echo.
echo Starting Next.js dev server on http://localhost:3000
echo.
call npm run dev
pause
