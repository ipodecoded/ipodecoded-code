#!/usr/bin/env bash
# ====================================================================
# IPODecoded (JournalDecoded.in) - One-Click Local Launcher
# Starts both FastAPI Backend (port 8000) and Vite Frontend (port 5173)
# ====================================================================

set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "🚀 Launching IPODecoded (JournalDecoded.in)"
echo "=================================================="

# 1. Activate Python virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating Python virtualenv..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
fi

# 2. Run initial pipeline update if database is empty
echo "Checking database status..."
python -m pipeline.runner

# 3. Trap exit signals to kill child background processes
trap 'echo "Stopping IPODecoded services..."; kill $(jobs -p) 2>/dev/null; exit' SIGINT SIGTERM EXIT

# 4. Start FastAPI backend on port 8000
echo "Starting FastAPI Backend on http://localhost:8000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 5. Start Vite frontend dev server on port 5173
echo "Starting Vite Frontend on http://localhost:5173..."
cd frontend
npm run dev -- --port 5173 --host &
FRONTEND_PID=$!

echo ""
echo "=================================================="
echo "✅ IPODecoded is LIVE:"
echo "👉 Frontend: http://localhost:5173"
echo "👉 API Docs: http://localhost:8000/docs"
echo "👉 Health:   http://localhost:8000/api/health"
echo "=================================================="
echo "Press Ctrl+C to stop all services."

# Wait for background processes
wait
