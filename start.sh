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
# Some venvs (especially those created by `uv venv` without --seed) ship
# without pip installed. If we naively run `pip install` we'd shell out to
# the system pip and hit PEP 668 (externally-managed-environment). Detect
# that and either bootstrap pip via ensurepip or fall back to `uv pip`.
# Pick requirements file. Default = requirements-min.txt (fast, ~2 min),
# which skips easyocr/torch (~1GB). Set WALLAS_FULL_INSTALL=1 for the full
# install with OCR support. We DO NOT use --quiet anywhere here — silencing
# pip on a fresh box leaves the user staring at "Ensuring dependencies..."
# for 15+ minutes thinking the script hung, while torch downloads in the
# dark. Show real progress instead so the user can see the download bar.
REQ_FILE="${WALLAS_DIR}/requirements-min.txt"
if [[ "${WALLAS_FULL_INSTALL:-0}" == "1" ]] || [[ ! -f "$REQ_FILE" ]]; then
  REQ_FILE="${WALLAS_DIR}/requirements.txt"
  echo "[INFO] Installing FULL dependencies (incl. easyocr/torch ~1GB). This will take 10-20 min on first run."
else
  echo "[INFO] Installing MIN dependencies (no OCR). Set WALLAS_FULL_INSTALL=1 if you need /v1/ocr/*."
fi

INSTALLER=""
if python -m pip --version >/dev/null 2>&1; then
  INSTALLER="pip"
else
  echo "[INFO] Venv has no pip — bootstrapping via ensurepip..."
  if python -m ensurepip --upgrade 2>/dev/null; then
    INSTALLER="pip"
  elif command -v uv >/dev/null 2>&1; then
    echo "[INFO] ensurepip not available; using 'uv pip' as installer."
    INSTALLER="uv"
  else
    echo "[ERROR] Venv has neither pip nor ensurepip, and 'uv' is not installed." >&2
    echo "        Fix: rm -rf '${VENV_DIR}' && uv venv --seed --python 3.12 '${VENV_DIR}'" >&2
    echo "        Or:  pip install --user --break-system-packages uv" >&2
    exit 1
  fi
fi

if [[ "$INSTALLER" == "pip" ]]; then
  python -m pip install --upgrade pip
  python -m pip install --progress-bar on -r "$REQ_FILE"
else
  uv pip install -r "$REQ_FILE"
fi

# ------------------------------------------------ native library preflight
# easyocr (OCR fallback) loads opencv at import time, which needs libGL and
# libglib at the system level. They are NOT pulled in by pip. On a fresh WSL2
# / Debian container the import fails with a cryptic
#   ImportError: libGL.so.1: cannot open shared object file
# Surface a friendly apt command up-front so the user knows exactly what to do.
# Non-fatal — chat/completion endpoints work without these libs; only the OCR
# pipeline and a few Camofox helpers need them.
MISSING_LIBS=()
if command -v ldconfig >/dev/null 2>&1; then
  ldconfig -p 2>/dev/null | grep -q "libGL.so.1"        || MISSING_LIBS+=("libgl1")
  ldconfig -p 2>/dev/null | grep -q "libglib-2.0.so.0"  || MISSING_LIBS+=("libglib2.0-0")
fi
if (( ${#MISSING_LIBS[@]} > 0 )); then
  echo "[WARN] Missing native libraries used by OCR / opencv: ${MISSING_LIBS[*]}"
  echo "       Install them with:  sudo apt install -y ${MISSING_LIBS[*]}"
  echo "       Chat/completion endpoints work without these — only /v1/ocr/* needs them."
fi

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
