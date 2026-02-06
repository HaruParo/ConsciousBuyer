#!/bin/bash

# Conscious Cart Coach - Start Script
# Starts both FastAPI backend and React frontend

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🛒 Starting Conscious Cart Coach..."
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Activate conda environment
CONDA_ENV="consciousbuyer"
if command -v conda &> /dev/null; then
    # Initialize conda for this shell
    eval "$(conda shell.bash hook)"

    if conda env list | grep -q "^$CONDA_ENV "; then
        echo "🐍 Activating conda environment: $CONDA_ENV"
        conda activate $CONDA_ENV
    else
        echo "⚠️  Conda environment '$CONDA_ENV' not found."
        echo "   Create it with: conda env create -f environments.yml"
        echo "   Or run: conda create -n $CONDA_ENV python=3.10"
        exit 1
    fi
else
    echo "⚠️  Conda not found. Using system Python."
fi

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
    echo "✓ Loaded environment variables"
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$SCRIPT_DIR/src"

# Check if frontend dependencies are installed
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    cd "$SCRIPT_DIR"
fi

# Start backend in background
echo "🔧 Starting FastAPI backend on http://localhost:8000..."
cd "$SCRIPT_DIR"
python -m uvicorn api.main:app --reload --port 8000 > /tmp/conscious-cart-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend dev server
echo "⚛️  Starting React frontend on http://localhost:5173..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/conscious-cart-frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Frontend: http://localhost:5173"
echo "  ✅ Backend:  http://localhost:8000"
echo "  ✅ API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/conscious-cart-backend.log"
echo "  Frontend: tail -f /tmp/conscious-cart-frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
