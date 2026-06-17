#!/usr/bin/env bash
# Start backend + frontend together. Keeps running until you Ctrl+C or run stop-platform.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs

if [[ ! -d venv ]]; then
  echo "ERROR: venv not found. Create it first: python -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
  exit 1
fi

if [[ ! -f backend/data/election_simulator.db ]] && [[ -z "${DATABASE_URL:-}" ]]; then
  echo "Loading database (first run)..."
  source venv/bin/activate
  PYTHONPATH="$ROOT" python backend/scripts/load_csvs_to_postgres.py
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

echo ""
echo "  Indian Election Intelligence Platform"
echo "  ─────────────────────────────────────"
echo "  Frontend:  http://127.0.0.1:5173"
echo "  Backend:   http://127.0.0.1:8000/docs"
echo "  Logs:      logs/backend.log  logs/frontend.log"
echo "  Stop:      ./scripts/stop-platform.sh  (or Ctrl+C)"
echo ""

source venv/bin/activate

# Kill anything already on our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

PYTHONPATH="$ROOT" uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload \
  >> logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

(cd frontend && npm run dev -- --host 127.0.0.1 >> "$ROOT/logs/frontend.log" 2>&1) &
FRONTEND_PID=$!
echo $FRONTEND_PID > logs/frontend.pid

cleanup() {
  echo ""
  echo "Stopping platform..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  rm -f logs/backend.pid logs/frontend.pid
  exit 0
}
trap cleanup INT TERM

# Wait until frontend responds
for i in {1..30}; do
  if curl -sf http://127.0.0.1:5173 >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Platform is running. Open http://127.0.0.1:5173"
echo "Press Ctrl+C to stop."

wait "$FRONTEND_PID"
