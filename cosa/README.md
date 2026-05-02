# WallasAPI + OpenClaw — Setup completo (Telegram, local)

Asistente personal en Telegram con WallasAPI como cerebro AI.

## Qué hace este setup

```
Tu Telegram → OpenClaw Gateway (localhost:18789) → WallasAPI (localhost:8001) → Groq/Gemini/etc.
```

- Le escribes a tu bot en Telegram
- OpenClaw recibe el mensaje y se lo manda a WallasAPI
- WallasAPI elige el provider más rápido y disponible
- Si un provider falla, hace fallback automático sin que notes nada
- La respuesta vuelve a tu Telegram en streaming

## Archivos en este paquete

| Archivo | Dónde va | Qué hace | Nota |
|---|---|---|---|
| `openclaw.json` | `~/.openclaw/openclaw.json` | Config de OpenClaw | **Copiar y editar token** |
| `SKILL.md` | `~/.openclaw/workspace/skills/wallasapi/SKILL.md` | Instrucciones del agente | **Copiar** — ya incluye fork, web search, diligence |
| `.env.example` | Raíz de wallasapi → copiar a `.env` | API keys | **Copiar y completar** — ahora incluye keys para web search |
| `start.sh` | Donde quieras | Inicia todo de un comando | **Opcional** — referencia para WSL/Linux |

> **Nota importante:** `api_server.py` y `streaming.py` en la raíz de wallasAPI **ya incluyen** circuit breaker, fork mode, web search dual backend, diligence compare y sticky routing. **No reemplaces el api_server.py actual** — ya es la versión más completa.

## Setup paso a paso

### 1. Crear bot de Telegram

1. Abre Telegram, busca `@BotFather`
2. Manda `/newbot`
3. Sigue las instrucciones — copia el **token** que te da

### 2. Obtener al menos una API key gratis

Recomendado empezar con **Groq** (más rápido, gratis):
- https://console.groq.com/keys → crea una key

O **Gemini** (también gratis, alta calidad):
- https://aistudio.google.com/apikey

### 3. Configurar WallasAPI

```bash
cd /ruta/a/wallasapi
cp .env.example .env
# Edita .env y pega tus API keys
```

Copia los archivos del setup:
```bash
mkdir -p services
cp streaming.py services/streaming.py
cp api_server.py api_server.py    # reemplaza el actual
```

Instala dependencias nuevas:
```bash
pip install httpx[http2] fastapi uvicorn pydantic python-dotenv
```

### 4. Configurar OpenClaw

```bash
# Instalar
npm install -g openclaw

# Copiar config
mkdir -p ~/.openclaw/workspace/skills/wallasapi
cp openclaw.json ~/.openclaw/openclaw.json
cp SKILL.md ~/.openclaw/workspace/skills/wallasapi/SKILL.md
```

Edita `~/.openclaw/openclaw.json` y reemplaza `REEMPLAZA_CON_TU_BOT_TOKEN_DE_BOTFATHER` con tu token de Telegram.

### 5. Iniciar todo

```bash
chmod +x start.sh
./start.sh
```

OpenClaw te mostrará un QR. Escanéalo con la app de Telegram para emparejar tu cuenta. Listo — ya puedes escribirle a tu bot.

## Verificar que funciona

```bash
# Health check de WallasAPI
curl http://localhost:8001/health

# Ver estado de providers
curl http://localhost:8001/v1/stats

# Probar chat sin Telegram
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hola"}],
    "stream": false
  }'
```

## Mejoras incluidas vs versión inicial

### Performance
- **httpx async + HTTP/2** — múltiples requests no se bloquean
- **Circuit breaker** — un provider caído se ignora 60s antes de reintentar
- **Cache de modelos 5 min** — `GET /v1/models` no martilla a los providers
- **Score dinámico** — el provider con menor latencia se usa primero

### Robustez
- **Fallback transparente** — si Groq falla, pasa a Gemini sin que el usuario note
- **Cancelación limpia** — si cierras Telegram, WallasAPI cancela el request
- **Rate limit por IP** — 60 req/min máx, evita abuso
- **Logging estructurado** — sabes exactamente qué provider respondió y cuánto tardó

### Telegram-específico
- **`X-Accel-Buffering: no`** — fuerza streaming real, sin buffering de proxies
- **Mensajes <4096 chars** — el SKILL.md le enseña a partir respuestas largas
- **Markdown compatible** — usa el formato que Telegram entiende
- **Pairing mode** — solo respondes a usuarios que escanearon tu QR

## Troubleshooting

**WallasAPI no arranca:**
```bash
tail -f wallasapi.log
```

**Telegram no responde:**
- Verifica que el token sea correcto
- Verifica que escanéaste el QR de pairing
- Verifica `curl http://localhost:8001/health`

**Respuestas lentas:**
- Check `curl http://localhost:8001/v1/stats` — mira qué provider está siendo usado
- Si Groq está caído, asegúrate de tener Gemini o GitHub Models como backup

**El stream se corta:**
- Probablemente es timeout del provider. Aumenta `READ_TIMEOUT` en `streaming.py`
- O pon un proxy entre Telegram y OpenClaw que no haga buffering

## Próximos pasos (cuando quieras escalar)

1. **Persistencia de memoria** — actualmente memory está en archivos locales. Migra a SQLite o Redis.
2. **Múltiples canales** — cuando funcione Telegram, agrega Discord/Slack en `openclaw.json`
3. **Deploy a VPS** — usa Caddy o nginx como reverse proxy con HTTPS
4. **Métricas con Prometheus** — exporta `/v1/stats` a Grafana
5. **Skills custom** — agrega skills específicos de Sparki en `~/.openclaw/workspace/skills/`
