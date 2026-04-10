@echo off
cls
echo.
echo ============================================
echo  AnomalySync Backend Server
echo ============================================
echo.
cd /d "%~dp0backend"

echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting FastAPI server on http://localhost:8000
echo.
python main.py
pause
