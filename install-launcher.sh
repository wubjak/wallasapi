#!/usr/bin/env bash
# Install a desktop launcher for WallasAPI on Linux.
#
# After running this, WallasAPI shows up in your application menu
# (Activities → Show Applications → "WallasAPI") so you can start the
# server with a single click — no need to open a terminal, activate
# the venv, or remember commands.
#
# Optionally, you can also drop a clickable shortcut on your Desktop.

set -euo pipefail

WALLAS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ---------------------------------------------------------------- guard rails
if [[ ! -f "$WALLAS_DIR/start.sh" ]]; then
  echo "[ERROR] start.sh not found in $WALLAS_DIR" >&2
  echo "        Run this script from your wallasAPI checkout." >&2
  exit 1
fi
chmod +x "$WALLAS_DIR/start.sh"
[[ -f "$WALLAS_DIR/stop.sh"  ]] && chmod +x "$WALLAS_DIR/stop.sh"

# ----------------------------------------------------------------- icon path
ICON_PATH=""
for candidate in logos/logoEN.png logos/logoES.png logos/socialbanner.png logo.png icon.png; do
  if [[ -f "$WALLAS_DIR/$candidate" ]]; then
    ICON_PATH="$WALLAS_DIR/$candidate"
    break
  fi
done
[[ -z "$ICON_PATH" ]] && ICON_PATH="utilities-terminal"

# ----------------------------------------------------------- terminal probe
# We need to launch start.sh inside a terminal so the user can see logs.
# `exec bash` at the end keeps the terminal open after the server exits
# so any error stays readable.
TERM_CMD=""
if command -v gnome-terminal >/dev/null 2>&1; then
  TERM_CMD="gnome-terminal --title=WallasAPI -- bash -c \"'$WALLAS_DIR/start.sh'; echo; echo '[Press Enter to close]'; read\""
elif command -v konsole >/dev/null 2>&1; then
  TERM_CMD="konsole --hold -e bash -c \"'$WALLAS_DIR/start.sh'\""
elif command -v xfce4-terminal >/dev/null 2>&1; then
  TERM_CMD="xfce4-terminal --hold --title=WallasAPI -e \"bash -c '$WALLAS_DIR/start.sh'\""
elif command -v xterm >/dev/null 2>&1; then
  TERM_CMD="xterm -hold -title WallasAPI -e \"'$WALLAS_DIR/start.sh'\""
else
  echo "[ERROR] No supported terminal emulator found." >&2
  echo "        Install one of: gnome-terminal, konsole, xfce4-terminal, xterm" >&2
  exit 1
fi

# ----------------------------------------------------------- write .desktop
APP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$APP_DIR/wallasapi.desktop"
STOP_DESKTOP_FILE="$APP_DIR/wallasapi-stop.desktop"
mkdir -p "$APP_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=WallasAPI
GenericName=AI Router
Comment=Start the multi-provider AI router (OpenAI · Anthropic · Ollama compatible)
Exec=$TERM_CMD
Icon=$ICON_PATH
Terminal=false
Categories=Development;Network;
Keywords=AI;LLM;OpenAI;Anthropic;Ollama;Gemini;Groq;router;proxy;
StartupNotify=true
StartupWMClass=WallasAPI
EOF
chmod 755 "$DESKTOP_FILE"

# Companion stop launcher (only if stop.sh exists)
if [[ -f "$WALLAS_DIR/stop.sh" ]]; then
  cat > "$STOP_DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Stop WallasAPI
GenericName=AI Router (stop)
Comment=Stop any running WallasAPI server on port 8001
Exec=bash -c "$WALLAS_DIR/stop.sh; sleep 1"
Icon=process-stop
Terminal=false
Categories=Development;Network;
Keywords=WallasAPI;stop;
EOF
  chmod 755 "$STOP_DESKTOP_FILE"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "[OK] Launcher installed:"
echo "       $DESKTOP_FILE"
[[ -f "$STOP_DESKTOP_FILE" ]] && echo "       $STOP_DESKTOP_FILE"
echo ""
echo "  -> Open Activities (Super key) and search 'WallasAPI'."
echo "  -> Right-click on the dock icon to 'Add to Favorites' / pin."
echo ""

# ------------------------------------------------------ optional Desktop copy
DESK=""
[[ -d "$HOME/Desktop"    ]] && DESK="$HOME/Desktop"
[[ -d "$HOME/Escritorio" ]] && DESK="$HOME/Escritorio"

if [[ -n "$DESK" ]]; then
  read -r -p "Place a clickable shortcut on your Desktop too? [Y/n] " yn
  yn="${yn:-Y}"
  if [[ "$yn" =~ ^[YySs] ]]; then
    cp "$DESKTOP_FILE" "$DESK/wallasapi.desktop"
    chmod +x "$DESK/wallasapi.desktop"
    # GNOME 40+ requires desktop files to be explicitly trusted
    if command -v gio >/dev/null 2>&1; then
      gio set "$DESK/wallasapi.desktop" "metadata::trusted" true 2>/dev/null || true
    fi
    echo "[OK] Desktop shortcut: $DESK/wallasapi.desktop"
    echo "     If it shows as a plain text file, right-click → 'Allow Launching'."
  fi
fi

echo ""
echo "Done. Single-click WallasAPI from Activities to start the server."
