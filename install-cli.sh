#!/usr/bin/env bash
# install-cli.sh — Pone `wallasapi` en el PATH del usuario.
#
# Corre esto UNA VEZ después de clonar el repo:
#
#   git clone https://github.com/wubjak/wallasapi.git
#   cd wallasapi
#   ./install-cli.sh
#
# A partir de ahí, podés llamar `wallasapi` desde cualquier lado.

set -euo pipefail

SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="$HOME/.local/bin"
LINK_PATH="$TARGET_DIR/wallasapi"

mkdir -p "$TARGET_DIR"

if [[ -L "$LINK_PATH" || -e "$LINK_PATH" ]]; then
  CURRENT="$(readlink -f "$LINK_PATH" 2>/dev/null || echo "")"
  EXPECTED="$SCRIPT_DIR/wallasapi"
  if [[ "$CURRENT" == "$EXPECTED" ]]; then
    echo "[OK] wallasapi ya está enlazado correctamente en $LINK_PATH"
  else
    echo "[INFO] Sobrescribiendo enlace antiguo ($CURRENT) con $EXPECTED"
    ln -sf "$EXPECTED" "$LINK_PATH"
  fi
else
  ln -s "$SCRIPT_DIR/wallasapi" "$LINK_PATH"
  echo "[OK] Enlace creado: $LINK_PATH -> $SCRIPT_DIR/wallasapi"
fi

# Asegurar que ~/.local/bin esté en el PATH (vía ~/.bashrc).
# Solo modificamos si la línea no existe ya.
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
if ! grep -Fq "$PATH_LINE" "$HOME/.bashrc" 2>/dev/null; then
  echo "" >> "$HOME/.bashrc"
  echo "# Added by wallasapi/install-cli.sh" >> "$HOME/.bashrc"
  echo "$PATH_LINE" >> "$HOME/.bashrc"
  echo "[OK] Agregado a ~/.bashrc — abrí una terminal nueva o corré: source ~/.bashrc"
else
  echo "[OK] ~/.local/bin ya estaba en el PATH de ~/.bashrc"
fi

echo ""
echo "Listo. Probá:"
echo "  wallasapi --help"
echo "  wallasapi          # arranca en foreground"
echo "  wallasapi start    # arranca en background"
