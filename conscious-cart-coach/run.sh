#!/bin/bash

# Conscious Cart Coach - Start Script
# Starts both FastAPI backend and React frontend

echo "🛒 Starting Conscious Cart Coach..."
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Loaded environment variables"
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(dirname "$0")/src"

# Start backend in background
echo "🔧 Starting FastAPI backend on http://localhost:8000..."
python -m uvicorn api.main:app --reload --port 8000 > /tmp/conscious-cart-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend (serving built static files)
echo "⚛️  Starting React frontend on http://localhost:5173..."
cd Figma_files/dist
python3 -m http.server 5173 > /tmp/frontend-static.log 2>&1 &
FRONTEND_PID=$!

sleep 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Frontend: http://localhost:5173"
echo "  ✅ Backend:  http://localhost:8000"
echo "  ✅ API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to stop
wait $FRONTEND_PID

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
