# Integración Gravedad ↔ WallasAPI

## Qué hace

Conecta Willaku Center / Gravedad con WallasAPI para usar:
- Modelos virtuales (`auto`, `rapido`, `standard`, `razonamiento`)
- Web search dual backend
- Fork mode (3 modelos en paralelo)
- Navegación stealth con camofox
- Diligence compare

## Requisitos

- WallasAPI corriendo en `http://localhost:8001`
- Gravedad corriendo (usualmente `http://localhost:5000`)
- `requests` instalado en el entorno de Gravedad

## Paso 1: Parchear backend

```bash
cd D:\ProyectoIG\wallasAPI\gravedad_integration
python patch_server.py
```

Esto modifica `../gravedad/server.py` añadiendo:
- Proxy endpoints `/v1/search/web`, `/v1/chat/completions/fork`, `/v1/diligence/compare`, `/v1/browser/*`
- Proxy condicional en `/chat`: si el modelo es virtual (`auto`, `rapido`, etc.), redirige a WallasAPI

## Paso 2: Parchear frontend

```bash
cd D:\ProyectoIG\wallasAPI\gravedad_integration
python patch_app_js.py
```

Esto modifica `../gravedad/static/app.js` añadiendo:
- Optgroup "Virtuales ⚡" al principio del selector de modelos
- Toggles UI: **🔍 Web** y **🍴 Fork Mode**

## Paso 3: Reiniciar Gravedad

```bash
cd D:\ProyectoIG\gravedad
python server.py
```

## Paso 4: Probar

1. Abre `http://localhost:5000` (o el puerto de Gravedad)
2. En el selector de modelos deberías ver **Virtuales ⚡** arriba de todo
3. Selecciona `auto` o `rapido`
4. Activa **🔍 Web** para enriquecer con búsqueda
5. Activa **🍴 Fork** para ejecutar múltiples modelos en paralelo

## Modelos virtuales

| Modelo | Qué hace |
|---|---|
| `auto` | Selecciona el mejor modelo disponible según circuit breaker y latencia |
| `rapido` | Elige el modelo más rápido (ideal para respuestas cortas) |
| `standard` | Equilibrio entre calidad y velocidad |
| `razonamiento` | Optimizado para razonamiento profundo y código |

## Endpoints proxy añadidos

- `GET /v1/models` → modelos de WallasAPI (incluye virtuales)
- `POST /v1/search/web` → búsqueda web dual backend
- `POST /v1/chat/completions/fork` → fork mode
- `POST /v1/diligence/compare` → comparar APIs
- `POST /v1/browser/open`, `/act`, `/search`, `/summarize` → camofox
- `POST /v1/browser/youtube/transcript` → transcripts

## Si algo falla

Los backups se guardan como:
- `gravedad/server.py.backup.wallas`
- `gravedad/static/app.js.backup.wallas`

Para restaurar:
```bash
cd D:\ProyectoIG\gravedad
copy server.py.backup.wallas server.py
copy static\app.js.backup.wallas static\app.js
```

## Nota sobre Telegram / OpenClaw

Si usas Gravedad Chat vía Telegram, OpenClaw ya puede usar WallasAPI directamente configurando:
- `baseURL`: `http://localhost:8001/v1`
- `model`: `auto` (o cualquier virtual)

Los toggles Web/Fork son solo para la UI web; OpenClaw/Gravedad Chat usan el campo `web_search`/`fork_mode` en el JSON del request.
