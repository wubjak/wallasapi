# AI Services v2.0 — Manual Técnico Completo

> **Paquete modular de ruteo inteligente de IA multi-proveedor.**
> Creado por Willen Ponce & Antigravity.

---

## 1. ¿Qué es AI Services?

`ai_services` es un paquete Python que actúa como un **router inteligente** entre múltiples proveedores de IA (LLMs). En lugar de conectarte directamente a una sola API, envías tu solicitud al router y éste:

1. **Selecciona el mejor modelo disponible** según capacidades requeridas (texto, visión, audio, etc.)
2. **Hace fallback automático** si un proveedor falla (429, timeout, error)
3. **Normaliza las respuestas** independientemente del proveedor usado
4. **Mantiene memoria** de la conversación entre mensajes

### ¿Para qué sirve?
- Usar IA gratis sin depender de un solo proveedor
- Tener un "super-provider" que agrega 500+ modelos
- Exponer una API compatible con OpenAI/Anthropic para herramientas externas (VSCode, Claude Code, etc.)
- Manejar multimodalidad (imágenes, audio, documentos) de forma transparente

---

## 2. Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   CLIENTES                          │
│  Playground │ Claude Code │ VSCode │ curl │ Apps    │
└──────────┬──────────┬──────────┬────────────────────┘
           │          │          │
           ▼          ▼          ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI (api_server.py)                 │
│  /v1/chat/completions  /v1/messages  /v1/models     │
│  /health               Auth: PROXY_API_KEY          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              AIRouter (router.py)                    │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Audio Detect  │  │ File Shim    │                 │
│  │ MP3→audio     │  │ PDF→texto    │                 │
│  └──────────────┘  └──────────────┘                 │
│  ┌──────────────────────────────────┐               │
│  │    Model Priority Engine         │               │
│  │  1. Free + Fast providers first  │               │
│  │  2. Capability matching          │               │
│  │  3. Auto-fallback on error       │               │
│  └──────────────────────────────────┘               │
└──────────────────────┬──────────────────────────────┘
                       │
     ┌─────────┬───────┼───────┬─────────┬────────┐
     ▼         ▼       ▼       ▼         ▼        ▼
  Cerebras   Groq   Gemini  SambaNova  GitHub  OpenRouter
  (ultra     (fast) (multi  (free)     (free)  (:free
   fast)            modal)                      models)
```

---

## 3. Proveedores Configurados

| Proveedor   | Base URL                              | Gratis | Visión | Audio | Archivos Nativos |
|-------------|---------------------------------------|--------|--------|-------|------------------|
| Cerebras    | api.cerebras.ai/v1                    | ✅     | ❌     | ❌    | ❌ (shim)        |
| Groq        | api.groq.com/openai/v1                | ✅     | ✅     | ✅*   | ❌ (shim)        |
| SambaNova   | api.sambanova.ai/v1                   | ✅     | ✅     | ❌    | ❌ (shim)        |
| Gemini      | SDK nativo (google-genai)             | ✅**   | ✅     | ✅    | ✅               |
| GitHub      | models.inference.ai.azure.com         | ✅     | ✅     | ❌    | ❌ (shim)        |
| Ollama      | localhost:11434                       | ✅     | ✅     | ❌    | ❌ (shim)        |
| OpenRouter  | openrouter.ai/api/v1                  | ✅***  | ✅     | ❌    | ❌ (shim)        |
| Mistral     | api.mistral.ai/v1                     | ❌     | ✅     | ❌    | ❌ (shim)        |
| Cohere      | api.cohere.ai/compatibility/v1        | ❌     | ❌     | ❌    | ❌ (shim)        |

*Groq tiene Whisper para audio. **Gemini Flash/Lite son gratis. ***OpenRouter tiene modelos `:free`.

---

## 4. Tipos de Modelos (Capabilities)

### Para Chat (usables en conversaciones)

| Flag       | Descripción                                                                 |
|------------|-----------------------------------------------------------------------------|
| `text`     | Modelo estándar de chat/completions. Puede responder preguntas.             |
| `vision`   | Puede analizar imágenes (fotos, screenshots, diagramas).                    |
| `audio`    | Puede procesar audio nativo (grabaciones, archivos MP3/WAV).                |
| `file`     | Soporta archivos/documentos nativamente (solo Gemini).                      |
| `file_shim`| Acepta documentos via conversión a texto (PDF→texto, etc.).                 |
| `reasoning`| Tiene "pensamiento" (chain-of-thought). Más lento pero más preciso.         |
| `code`     | Optimizado para generación de código.                                       |
| `moe`      | Mixture of Experts. Modelos grandes pero eficientes.                        |
| `free`     | Disponible sin costo.                                                       |

### No-Chat (herramientas especializadas)

| Flag       | Descripción                                                                 |
|------------|-----------------------------------------------------------------------------|
| `embedding`| Convierte texto en vectores numéricos. Sirve para búsqueda semántica, RAG.  |
| `rerank`   | Reordena resultados de búsqueda por relevancia. Sirve para mejorar RAG.     |
| `tts`      | Text-to-Speech. Convierte texto a audio hablado.                            |

---

## 5. File Shim (Conversión Automática de Archivos)

Cuando un usuario envía un archivo (PDF, TXT, JSON, etc.) a un modelo que **no soporta archivos nativamente**, el router automáticamente:

1. Extrae el texto del archivo (PDF→texto, JSON→texto, etc.)
2. Lo inyecta en el system prompt como contexto
3. Envía una notificación visual: `"⚠️ El modelo no soporta archivos nativamente. Se convirtieron a texto."`

Solo Gemini puede recibir archivos binarios directamente.

---

## 6. Auto-Detección de Audio

Cuando un usuario sube un archivo MP3/WAV/OGG por el botón de archivos (📎), el router:

1. Detecta que el MIME type es de audio (`audio/mpeg`, `audio/wav`, etc.)
2. Lo reclasifica automáticamente como input de audio
3. Lo envía a un modelo con capacidad `audio` (como Gemini)

Esto evita que el sistema intente "extraer texto" de un MP3.

---

## 7. Priorización de Modelos

Al iniciar, los modelos se ordenan por velocidad y costo:

1. **Free + Fast** → Cerebras, Groq, SambaNova
2. **Free + Multimodal** → Gemini (Flash/Lite), GitHub
3. **Free agregados** → OpenRouter `:free`, Ollama Cloud
4. **De pago** → Mistral, Cohere, OpenRouter premium
5. **Non-chat** → Embeddings, Rerank, TTS (al final)

Cuando el usuario envía un mensaje sin elegir modelo, el primero libre y rápido responde.

---

## 8. Estructura de Archivos

```
ai_services/
├── __init__.py           # Carga .env, exports públicos
├── api_server.py         # FastAPI (OpenAI/Anthropic endpoints)
├── config.py             # Proveedores, capabilities, constantes
├── router.py             # Orquestador principal
├── model_fetcher.py      # Descubrimiento dinámico de modelos
├── memory.py             # Persistencia de conversaciones
├── file_utils.py         # Extracción de texto + File Shim
├── search_tool.py        # Búsqueda web DuckDuckGo
├── logger.py             # Logging centralizado
├── .env                  # API Keys (NO subir a git)
├── requirements.txt      # Dependencias con versiones mínimas
├── start_proxy.bat       # Lanzador Windows
├── temp_context/         # Historiales de conversación (JSON)
├── MANUAL.md             # Este archivo
└── README.md             # Descripción general
```

---

## 9. Cómo Iniciar

```bash
# Opción A: Desde la raíz del proyecto
python start_proxy.py
# o
start_proxy.bat

# Opción B: Desde ai_services/
cd ai_services
start_proxy.bat
```

El servidor arranca en `http://localhost:8000`.

### Endpoints

| Método | Endpoint                | Formato   | Auth     |
|--------|-------------------------|-----------|----------|
| GET    | `/health`               | —         | No       |
| GET    | `/v1/models`            | OpenAI    | Sí*      |
| POST   | `/v1/chat/completions`  | OpenAI    | Sí*      |
| POST   | `/v1/messages`          | Anthropic | Sí*      |

*Si `PROXY_API_KEY` está configurado en `.env`, se requiere `Authorization: Bearer <key>`.

---

## 10. Seguridad (Dual Mode)

### Modo Local (desarrollo)
Si **no** configuras `PROXY_API_KEY` en `.env`, el proxy opera en modo abierto. Cualquiera en la red local puede usarlo.

### Modo VPS (producción)
Si configuras `PROXY_API_KEY=mi_key_secreta` en `.env`, todos los endpoints (excepto `/health`) requieren:
```
Authorization: Bearer mi_key_secreta
```

---

## 11. Uso desde Herramientas Externas

### Claude Code / Cline / Roo
```bash
# Configurar la base URL a tu proxy
export ANTHROPIC_BASE_URL=http://localhost:8000/v1
export ANTHROPIC_API_KEY=tu_proxy_api_key
```

### OpenAI SDK
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="tu_proxy_api_key")
response = client.chat.completions.create(
    model="gpt-4o",  # Se resuelve via alias al mejor modelo disponible
    messages=[{"role": "user", "content": "Hola!"}]
)
```

---

## 12. Cómo se Construyó (Historia)

### v1.0 (Abril 2026, primeras versiones)
- Router básico con Groq + Gemini + Ollama
- Memoria por archivos JSON
- Playground con Flask

### v2.0 (Abril 10 2026, reconstrucción completa)
- 9 proveedores con descubrimiento dinámico de modelos
- FastAPI como proxy OpenAI/Anthropic compatible
- File Shim con notificación visual
- Auto-detección de audio en archivos
- Categorías expandidas: Embedding, Rerank, TTS, Code
- Priorización inteligente por velocidad y costo
- Logging centralizado (sin print())
- Seguridad dual (local + VPS con API key)
- Fix del bucle infinito del .bat
- GitHub: extracción correcta de nombres de modelo (campo `name`, no `id`)
