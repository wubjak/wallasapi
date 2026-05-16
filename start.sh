#!/usr/bin/env bash
# WallasAPI launcher for Linux / macOS.
# Creates a venv if missing, installs requirements, frees port 8001 if held,
# then runs api_server.py. Idempotent — safe to re-run anytime.

set -euo pipefail

# Resolve the directory this script lives in so it works regardless of CWD.
WALLAS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$WALLAS_DIR"

# ---------------------------------------------------------------- venv setup
VENV_DIR="${WALLAS_DIR}/.venv"

# Pick a Python: prefer python3, fall back to python.
PY_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PY_BIN" ]]; then
  echo "[ERROR] No python3 / python found in PATH." >&2
  echo "        On Debian/Ubuntu: sudo apt install -y python3 python3-venv python3-pip" >&2
  exit 1
fi

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "[INFO] Creating virtual environment at ${VENV_DIR}"
  if ! "$PY_BIN" -m venv "$VENV_DIR" 2>/tmp/wallas-venv-err.log; then
    echo "[ERROR] python -m venv failed. Possible fixes:" >&2
    echo "  - Debian/Ubuntu: sudo apt install -y python3-venv python3-pip" >&2
    echo "  - Or use a stable Python: sudo apt install -y python3.12 python3.12-venv" >&2
    echo "                            then run: python3.12 -m venv .venv && source .venv/bin/activate" >&2
    echo "  - Or without sudo: pip install --user --break-system-packages uv && uv venv .venv" >&2
    echo "" >&2
    echo "Raw error from venv:" >&2
    cat /tmp/wallas-venv-err.log >&2
    exit 1
  fi
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# --------------------------------------------------------------- dependencies
echo "[INFO] Ensuring dependencies are installed..."
pip install --quiet --upgrade pip
pip install --quiet -r "${WALLAS_DIR}/requirements.txt"

# ----------------------------------------------------------- free port 8001
PORT="${WALLAS_PORT:-8001}"
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti:"$PORT" 2>/dev/null || true)
  if [[ -n "$PIDS" ]]; then
    echo "[INFO] Port ${PORT} is busy (pids: $PIDS). Killing previous instance..."
    kill -TERM $PIDS 2>/dev/null || true
    sleep 1
    kill -KILL $PIDS 2>/dev/null || true
  fi
elif command -v fuser >/dev/null 2>&1; then
  fuser -k "${PORT}/tcp" 2>/dev/null || true
fi

# ------------------------------------------------------------------- launch
export PYTHONPATH="${WALLAS_DIR}/..:${PYTHONPATH:-}"

cat <<BANNER
============================================================
  WallasAPI starting at  http://localhost:${PORT}
  Interactive docs:      http://localhost:${PORT}/docs
  Health check:          http://localhost:${PORT}/health
  Press Ctrl+C to stop.
============================================================
BANNER

exec python "${WALLAS_DIR}/api_server.py"
