#!/usr/bin/env bash
# Stop any WallasAPI server listening on port 8001 (or $WALLAS_PORT).

set -u

PORT="${WALLAS_PORT:-8001}"

stopped=0

if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -ti:"$PORT" 2>/dev/null || true)"
  if [[ -n "$PIDS" ]]; then
    echo "[INFO] Stopping WallasAPI on port $PORT (pids: $PIDS)..."
    kill -TERM $PIDS 2>/dev/null || true
    sleep 1
    # Force-kill any survivors
    kill -KILL $PIDS 2>/dev/null || true
    stopped=1
  fi
elif command -v fuser >/dev/null 2>&1; then
  if fuser -s "${PORT}/tcp" 2>/dev/null; then
    echo "[INFO] Stopping WallasAPI on port $PORT..."
    fuser -k "${PORT}/tcp" 2>/dev/null || true
    stopped=1
  fi
else
  echo "[WARN] Neither 'lsof' nor 'fuser' found. Install one:"
  echo "       sudo apt install -y lsof"
  exit 1
fi

if [[ "$stopped" -eq 1 ]]; then
  echo "[OK] WallasAPI stopped."
else
  echo "[INFO] No WallasAPI server was running on port $PORT."
fi
