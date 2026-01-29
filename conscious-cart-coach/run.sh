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

# Start frontend
echo "⚛️  Starting React frontend on http://localhost:5173..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

cd Figma_files
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
