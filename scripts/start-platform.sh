#!/usr/bin/env bash
# Run platform in background (survives terminal close). Use stop-platform.sh to stop.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs

# Stop any existing instance first
"$ROOT/scripts/stop-platform.sh" 2>/dev/null || true

if [[ ! -d venv ]]; then
  echo "ERROR: venv not found."
  exit 1
fi

if [[ ! -f backend/data/election_simulator.db ]] && [[ -z "${DATABASE_URL:-}" ]]; then
  source venv/bin/activate
  PYTHONPATH="$ROOT" python backend/scripts/load_csvs_to_postgres.py
fi

source venv/bin/activate

PYTHONPATH="$ROOT" nohup uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload \
  >> logs/backend.log 2>&1 &
echo $! > logs/backend.pid

cd frontend
nohup npm run dev -- --host 127.0.0.1 >> "$ROOT/logs/frontend.log" 2>&1 &
echo $! > "$ROOT/logs/frontend.pid"
cd "$ROOT"

echo "Platform started in background."
echo "  Open: http://127.0.0.1:5173"
echo "  Stop: ./scripts/stop-platform.sh"
echo "  Logs: tail -f logs/backend.log logs/frontend.log"
