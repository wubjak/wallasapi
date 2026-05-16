#!/bin/bash
# start.sh — Inicia WallasAPI + OpenClaw para Telegram
# Uso: chmod +x start.sh && ./start.sh

set -e

# ─── Colores ───
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${GREEN}━━━ WallasAPI + OpenClaw ━━━${NC}"

# ─── 1. Verificar .env ───
if [ ! -f .env ]; then
    echo -e "${RED}✗ No existe .env. Copia .env.example a .env y configura las API keys.${NC}"
    exit 1
fi

# ─── 2. Verificar al menos una API key ───
if ! grep -E "^(GROQ_API_KEY|GEMINI_API_KEY|GITHUB_TOKEN|OPENROUTER_API_KEY)=.+" .env > /dev/null; then
    echo -e "${RED}✗ Configura al menos una API key en .env${NC}"
    exit 1
fi

# ─── 3. Verificar OpenClaw instalado ───
if ! command -v openclaw &> /dev/null; then
    echo -e "${YELLOW}⚠ OpenClaw no instalado. Instalando...${NC}"
    npm install -g openclaw
fi

# ─── 4. Verificar config de OpenClaw ───
if [ ! -f ~/.openclaw/openclaw.json ]; then
    echo -e "${YELLOW}⚠ Falta ~/.openclaw/openclaw.json — copiándolo${NC}"
    mkdir -p ~/.openclaw/workspace/skills/wallasapi
    cp openclaw.json ~/.openclaw/openclaw.json
    cp SKILL.md ~/.openclaw/workspace/skills/wallasapi/SKILL.md
    echo -e "${RED}✗ Edita ~/.openclaw/openclaw.json y agrega tu Telegram bot token de @BotFather${NC}"
    exit 1
fi

# ─── 5. Verificar token de Telegram ───
if grep -q "REEMPLAZA_CON_TU_BOT_TOKEN" ~/.openclaw/openclaw.json; then
    echo -e "${RED}✗ Edita ~/.openclaw/openclaw.json y agrega tu Telegram bot token de @BotFather${NC}"
    exit 1
fi

# ─── 6. Iniciar WallasAPI en background ───
echo -e "${GREEN}▶ Iniciando WallasAPI en :8001...${NC}"
python -m wallasAPI.api_server > wallasapi.log 2>&1 &
WALLAS_PID=$!

# Esperar a que esté listo
for i in {1..10}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ WallasAPI listo${NC}"
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${RED}✗ WallasAPI no arrancó. Revisa wallasapi.log${NC}"
    kill $WALLAS_PID 2>/dev/null
    exit 1
fi

# ─── 7. Iniciar OpenClaw Gateway ───
echo -e "${GREEN}▶ Iniciando OpenClaw Gateway...${NC}"
echo -e "${YELLOW}  Escanea el código QR que aparece para emparejar tu Telegram${NC}"

trap "echo -e '\n${YELLOW}Cerrando...${NC}'; kill $WALLAS_PID 2>/dev/null; exit 0" INT TERM

openclaw gateway

# Cleanup al salir
kill $WALLAS_PID 2>/dev/null
