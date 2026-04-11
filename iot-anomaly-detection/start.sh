#!/bin/bash

echo "🚀 Starting Anomaly Detection System..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo "${BLUE}[1/4] Checking prerequisites...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.9+ is required"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 18+ is required"
    exit 1
fi
echo "${GREEN}✅ All prerequisites found${NC}"

# Setup backend
echo ""
echo "${BLUE}[2/4] Setting up backend...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate 2>/dev/null || venv\Scripts\activate 2>/dev/null
pip install -r requirements.txt > /dev/null 2>&1
echo "${GREEN}✅ Backend dependencies installed${NC}"

# Start backend
echo ""
echo "${BLUE}[3/4] Starting backend server...${NC}"
echo "📡 Backend starting on http://localhost:8000"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3

# Setup & start frontend
echo ""
echo "${BLUE}[4/4] Setting up frontend...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1
fi
echo "${GREEN}✅ Frontend dependencies installed${NC}"

echo ""
echo "${GREEN}✅ System started successfully!${NC}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "📡 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
npm run dev

# Cleanup
kill $BACKEND_PID 2>/dev/null
