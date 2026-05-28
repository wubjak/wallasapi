#!/usr/bin/env bash
# Update WallasAPI: git pull, refresh deps, restart server.
# Safe to re-run anytime. Preserves your .env (gitignored) and venv (idempotent).
#
# Used by the `wallasapi update` subcommand, but also runnable directly
# from a clone:  ./update.sh

set -u

WALLAS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$WALLAS_DIR"

PORT="${WALLAS_PORT:-8001}"

# ---------------------------------------------------------------- preconditions
if [[ ! -d .git ]]; then
  echo "[ERROR] $WALLAS_DIR is not a git repo — cannot update from git." >&2
  echo "        Clone with: git clone https://github.com/wubjak/wallasapi.git wallasAPI" >&2
  exit 1
fi

# Refuse to overwrite local changes silently — the user has been there before.
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo "[WARN] Working tree has local changes:"
  git status --short
  echo ""
  read -r -p "Stash them and continue? [y/N] " yn
  case "$yn" in
    [yYsS]*)
      git stash push -u -m "wallasapi-update auto-stash $(date +%Y%m%d_%H%M%S)"
      echo "[INFO] Changes stashed. Recover with: git stash pop"
      ;;
    *)
      echo "[ABORT] Resolve local changes first (git stash, git commit, or git checkout)."
      exit 1
      ;;
  esac
fi

# ---------------------------------------------------------------- git pull
echo "[INFO] Fetching from origin..."
git fetch origin --quiet

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
BEHIND="$(git rev-list "HEAD..origin/${BRANCH}" --count 2>/dev/null || echo 0)"

if [[ "$BEHIND" -eq 0 ]]; then
  echo "[INFO] Already on the latest commit ($(git log -1 --oneline))"
  ALREADY_UP_TO_DATE=1
else
  echo "[INFO] $BEHIND new commit(s) on origin/$BRANCH. Pulling..."
  git pull --ff-only origin "$BRANCH"
  ALREADY_UP_TO_DATE=0
fi

# ---------------------------------------------------------------- venv + deps
# Refresh deps only when something actually changed (requirements.txt or the
# venv doesn't exist yet). On a no-op pull this finishes in ~50ms.
NEED_DEPS_REFRESH=0
if [[ ! -d .venv ]]; then
  NEED_DEPS_REFRESH=1
elif [[ "$ALREADY_UP_TO_DATE" -eq 0 ]] && git diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -q "^requirements.txt$"; then
  echo "[INFO] requirements.txt changed in this update — refreshing venv deps..."
  NEED_DEPS_REFRESH=1
fi

if [[ "$NEED_DEPS_REFRESH" -eq 1 ]]; then
  # Delegate to start.sh's bootstrap (handles uv/pip/ensurepip fallbacks).
  # Suppress the actual launch by short-circuiting before exec.
  echo "[INFO] Bootstrapping venv via start.sh..."
  # start.sh will (re)create venv and pip-install but also tries to launch
  # the server. We don't want that here — run it in a subshell and stop
  # before the exec by replacing the final `exec python` with `true`.
  bash -c '
    set -e
    cd "$1"
    # mini-bootstrap, mirrors start.sh up to the launch
    PY_BIN=""
    for c in python3 python3.13 python3.12 python3.11 python3.10 python; do
      if command -v "$c" >/dev/null 2>&1 && "$c" -c "import venv, ensurepip" >/dev/null 2>&1; then
        PY_BIN="$c"; break
      fi
    done
    [[ -z "$PY_BIN" ]] && { echo "[ERROR] No usable Python found" >&2; exit 1; }
    [[ ! -f .venv/bin/activate ]] && "$PY_BIN" -m venv .venv
    .venv/bin/python -m pip install --quiet --upgrade pip 2>/dev/null || true
    .venv/bin/python -m pip install --quiet -r requirements.txt 2>/dev/null \
      || (command -v uv >/dev/null 2>&1 && uv pip install --quiet --python .venv/bin/python -r requirements.txt) \
      || { echo "[ERROR] Failed to install requirements" >&2; exit 1; }
  ' _ "$WALLAS_DIR"
fi

# ---------------------------------------------------------------- restart
if command -v lsof >/dev/null 2>&1; then
  RUNNING_PIDS="$(lsof -ti:"$PORT" 2>/dev/null || true)"
else
  RUNNING_PIDS=""
fi

if [[ -n "$RUNNING_PIDS" ]]; then
  if [[ "$ALREADY_UP_TO_DATE" -eq 1 && "$NEED_DEPS_REFRESH" -eq 0 ]]; then
    echo "[INFO] Nothing to update. Server is already running on :$PORT (pids: $RUNNING_PIDS) — leaving it alone."
    exit 0
  fi
  echo "[INFO] Stopping current server (pids: $RUNNING_PIDS)..."
  kill -TERM $RUNNING_PIDS 2>/dev/null || true
  sleep 2
  kill -KILL $RUNNING_PIDS 2>/dev/null || true
fi

echo "[INFO] Starting server in background..."
nohup "$WALLAS_DIR/start.sh" > /tmp/wallas.log 2>&1 &
disown

# Wait up to 25s for the port to bind (model registry load can take ~10s).
for i in $(seq 1 25); do
  if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "[OK] WallasAPI listening on :$PORT — now on $(git log -1 --oneline)"
    echo "     Logs: tail -f /tmp/wallas.log"
    exit 0
  fi
  sleep 1
done

echo "[WARN] Server hasn't bound :$PORT after 25s. Last 20 log lines:"
tail -20 /tmp/wallas.log 2>/dev/null
exit 1
