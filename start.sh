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

# Allow the user to force a specific Python via `PYTHON=python3.12 ./start.sh`.
# Otherwise probe a list of known-good interpreters and pick the first one
# whose `venv` module actually works (modern Debian/Ubuntu ship Python with
# venv split into a separate apt package, and bleeding-edge versions like
# 3.14 may not have the corresponding `pythonX.Y-venv` packaged yet).
CANDIDATES=()
if [[ -n "${PYTHON:-}" ]]; then
  CANDIDATES+=("$PYTHON")
fi
CANDIDATES+=("python3" "python3.13" "python3.12" "python3.11" "python3.10" "python")

PY_BIN=""
for c in "${CANDIDATES[@]}"; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import venv, ensurepip' >/dev/null 2>&1; then
      PY_BIN="$c"
      break
    fi
  fi
done

if [[ -z "$PY_BIN" ]]; then
  echo "[ERROR] No Python interpreter with a working venv module was found." >&2
  echo "        Tried: ${CANDIDATES[*]}" >&2
  echo "" >&2
  echo "Fixes (pick the one that fits your environment):" >&2
  echo "  - Debian/Ubuntu (recommended): sudo apt install -y python3.12 python3.12-venv" >&2
  echo "                                 then re-run ./start.sh" >&2
  echo "  - Generic apt: sudo apt install -y python3 python3-venv python3-pip" >&2
  echo "  - Without sudo: pip install --user --break-system-packages uv && uv venv .venv" >&2
  echo "                  then: source .venv/bin/activate && uv pip install -r requirements.txt" >&2
  exit 1
fi

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  PY_VER="$("$PY_BIN" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "[INFO] Creating virtual environment at ${VENV_DIR} using ${PY_BIN} (${PY_VER})"
  if ! "$PY_BIN" -m venv "$VENV_DIR" 2>/tmp/wallas-venv-err.log; then
    echo "[ERROR] '${PY_BIN} -m venv' failed unexpectedly. Raw error:" >&2
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
