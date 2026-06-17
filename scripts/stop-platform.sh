#!/usr/bin/env bash
# Stop background platform processes
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f logs/backend.pid ]]; then
  kill "$(cat logs/backend.pid)" 2>/dev/null || true
  rm -f logs/backend.pid
fi
if [[ -f logs/frontend.pid ]]; then
  kill "$(cat logs/frontend.pid)" 2>/dev/null || true
  rm -f logs/frontend.pid
fi

lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo "Platform stopped."
