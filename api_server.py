"""
WallasAPI-OpenClaw Edition v4.0
Enrutador de IA optimizado 100% para OpenClaw.
Expone endpoints OpenAI-compatible con mejoras específicas para compatibilidad
de agentes CLI como OpenClaw, Claude Code, y herramientas similares.

Mejoras sobre wallasAPI original:
- Model listing 100% compatible OpenAI (object, permission, root, parent)
- Streaming SSE con keep-alive para evitar timeouts en agentes
- Soporte completo de tool_calls / function_calling
- Manejo de system messages según especificación OpenAI
- Endpoint /v1/models/{model} con metadata completa
- Headers CORS optimizados para conexiones locales
- Logging silencioso en modo agente para no contaminar stdout
"""
import os
import sys
import time
import uuid
import json
import asyncio
import threading
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Union

from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# =============================================================================
# Core imports — wallasAPI package
# =============================================================================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wallasAPI.router import AIRouter
from wallasAPI.config import MODELS_REGISTRY, PROVIDERS, PROVIDER_METADATA, PROXY_API_KEY_ENV
from wallasAPI.model_fetcher import (
    update_registry_async, load_registry_from_cache,
    verify_models_alive, cache_needs_verify,
)
from wallasAPI.search_engine import get_search_engine
from wallasAPI.browser_engine import get_browser_client
from wallasAPI.logger import log

from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# CONFIGURACIÓN OPENCLAW
# =============================================================================
OPENCLAW_MODE = os.getenv("WALLAS_OPENCLAW_MODE", "true").lower() in ("1", "true", "yes")
SILENT_AGENT_LOGS = os.getenv("WALLAS_SILENT_AGENT", "true").lower() in ("1", "true", "yes")
PORT = int(os.getenv("WALLAS_PORT", "8001"))
HOST = os.getenv("WALLAS_HOST", "0.0.0.0")

if SILENT_AGENT_LOGS and OPENCLAW_MODE:
    # Reducir ruido de logs cuando OpenClaw hace polling de /v1/models
    import logging
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("[WALLAS-OPENCLAW] Iniciando WallasAPI-OpenClaw Edition...")
    has_cache = load_registry_from_cache()
    if has_cache:
        log.info(f"[READY] Caché cargada: {len(MODELS_REGISTRY)} modelos.")
        asyncio.create_task(update_registry_async())
    else:
        log.info("[FETCH] Descargando modelos por primera vez...")
        await update_registry_async()
        log.info(f"[READY] {len(MODELS_REGISTRY)} modelos cargados.")

    # Background health probe of the catalog if it's never been verified
    # or hasn't been re-checked in the last WALLAS_VERIFY_AT_STARTUP seconds.
    if cache_needs_verify():
        log.info("[VERIFY] Cache stale or unverified; running health probe in background.")
        asyncio.create_task(verify_models_alive())

    yield
    log.info("[SHUTDOWN] WallasAPI-OpenClaw detenido.")


app = FastAPI(
    title="WallasAPI - Your better and friendly AI router",
    description="Multi-provider AI router. OpenAI · Anthropic · Ollama-compatible gateway with auto-fallback, streaming, multimodal, and circuit-breaker observability.",
    version="4.1.0",
    lifespan=lifespan,
)

# CORS permisivo para localhost / LAN (OpenClaw puede estar en WSL, Docker, o nativo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = AIRouter()


# =============================================================================
# Auth
# =============================================================================

def _get_proxy_api_key() -> Optional[str]:
    return os.getenv(PROXY_API_KEY_ENV)

async def verify_auth(authorization: Optional[str] = Header(None)):
    expected = _get_proxy_api_key()
    if not expected:
        return
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "").strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")


# =============================================================================
# Request Models (Pydantic) — 100% OpenAI spec
# =============================================================================

class OpenAI_Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class OpenAI_ChatRequest(BaseModel):
    model: str
    messages: List[OpenAI_Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    # OpenClaw/Claude Code envían esto a veces
    thinking: Optional[Union[str, Dict[str, Any]]] = None
    web_search: Optional[bool] = False


class Anthropic_Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class Anthropic_Request(BaseModel):
    model: str
    messages: List[Anthropic_Message]
    system: Optional[str] = None
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    thinking: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "text-embedding-3-small"


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


class WebSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    backend: Optional[str] = "auto"  # auto, duckduckgo, google_cse, serpapi


class ForkChatRequest(BaseModel):
    model: str  # virtual model: auto, rapido, standard, razonamiento, or specific
    messages: List[OpenAI_Message]
    max_parallel: Optional[int] = 3
    return_all: Optional[bool] = False
    web_search: Optional[bool] = False


class DiligenceCompareRequest(BaseModel):
    task: str
    system_prompt: Optional[str] = "Eres un asistente experto."
    max_parallel: Optional[int] = 3
    criteria: Optional[str] = "calidad"  # calidad, velocidad, costo


class BrowserOpenRequest(BaseModel):
    url: str
    user_id: Optional[str] = "wallasapi_default"
    session_key: Optional[str] = None


class BrowserActRequest(BaseModel):
    tab_id: str
    action: str  # snapshot, click, type, scroll, press, screenshot, links, close
    ref: Optional[str] = None       # for click / type
    text: Optional[str] = None      # for type
    key: Optional[str] = None       # for press
    press_enter: Optional[bool] = False
    user_id: Optional[str] = "wallasapi_default"


class BrowserSearchRequest(BaseModel):
    query: str
    macro: Optional[str] = "@google_search"
    user_id: Optional[str] = "wallasapi_default"
    max_results_pages: Optional[int] = 3


class YouTubeTranscriptRequest(BaseModel):
    url: str
    languages: Optional[List[str]] = None


def extract_clean_search_query(prompt: str) -> str:
    """
    Extrae términos de búsqueda limpios en español, removiendo verbos conversacionales,
    preposiciones, pronombres y stopwords, y quitando acentos para máxima compatibilidad con motores de búsqueda.
    """
    if not prompt:
        return ""
    # 1. Convertir a minúsculas y quitar acentos
    query = prompt.lower()
    accents = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}
    for acc, clean_char in accents.items():
        query = query.replace(acc, clean_char)
        
    # 2. Quitar puntuación común
    for char in ["?", "¿", "!", "¡", ",", ".", ";", ":", "\"", "'", "(", ")", "-", "_"]:
        query = query.replace(char, " ")
        
    # 3. Stopwords y palabras ruidosas conversacionales en español
    blacklist = {
        # preposiciones / conjunciones
        "de", "la", "el", "en", "y", "a", "los", "un", "una", "unos", "unas", 
        "con", "por", "para", "sobre", "entre", "desde", "hasta", "sin", "tras", "o", "u", "e",
        # pronombres
        "que", "este", "esta", "esto", "estos", "estas", "aquel", "aquella",
        "me", "te", "se", "nos", "os", "lo", "le", "les", "mi", "tu", "su", "sus", "como", "cual", "cuales",
        # verbos conversacionales / peticiones
        "hola", "busca", "buscar", "googlea", "dime", "saber", "quiero", "puedes", 
        "encuentra", "encontrar", "diga", "digame", "pido", "pedi", "pregunta", "consultar", "consulta",
        # ruido de instrucciones de búsqueda
        "internet", "web", "google", "favor", "actualizado", "actualizada", "informacion", "datos", "hoy", "actual",
        "dia", "tiempo", "real", "siguiente", "usuario"
    }
    
    words = query.split()
    filtered_words = [w for w in words if w not in blacklist and len(w) > 1]
    
    # Si la lista queda vacía o muy corta, usamos una limpieza más permisiva
    if len(filtered_words) < 2:
        basic_blacklist = {"hola", "busca", "buscar", "en", "la", "el", "de", "y", "internet", "web"}
        filtered_words = [w for w in words if w not in basic_blacklist]
        
    cleaned = " ".join(filtered_words).strip()
    return cleaned if cleaned else prompt


def _sanitize_tools(tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """Drop tool entries missing a valid function name.

    NVIDIA NIM (and most strict OpenAI-compatible backends) reject the whole
    request with 400 when any tool in the array has an empty/missing
    `function.name`. A single malformed tool from the client therefore
    cascades through every Mistral/strict model in the registry until the
    router falls back to a lenient one (Gemini), which silently accepts the
    bad payload and produces low-quality replies.
    """
    if not tools:
        return tools
    clean = []
    dropped = 0
    for t in tools:
        if not isinstance(t, dict):
            dropped += 1
            continue
        fn = t.get("function") or {}
        name = (fn.get("name") or "").strip()
        if not name:
            dropped += 1
            continue
        clean.append(t)
    if dropped:
        log.warning(f"[TOOLS] Sanitized {dropped} tool(s) with empty/missing function.name")
    return clean or None


def _normalize_messages_for_openclaw(messages: List[OpenAI_Message]) -> tuple:
    """
    Normaliza mensajes OpenAI para el router interno.
    Extrae system prompt y convierte history a listas de dicts.
    """
    system_prompt = "You are a helpful assistant."
    cleaned_messages = []
    tools = None
    tool_choice = None

    for m in messages:
        if m.role == "system":
            system_prompt = m.content if isinstance(m.content, str) else str(m.content)
        elif m.role in ("user", "assistant", "tool"):
            # Build dict WITHOUT None-valued fields. Strict OpenAI validators
            # downstream (notably NVIDIA NIM Nemotron, which runs vLLM with
            # pydantic strict discriminated unions) reject `name: null`,
            # `tool_calls: null`, `tool_call_id: null` and return HTTP 400
            # with "Input should be a valid string / iterable" errors that
            # circuit-break a perfectly good model out of the routing pool.
            # Other providers (OpenAI, Gemini, Groq) tolerate the Nones but
            # gain nothing from them, so just omit at the source.
            msg_dict = {
                "role": m.role,
                "content": m.content if isinstance(m.content, str) else str(m.content),
            }
            if m.name is not None:
                msg_dict["name"] = m.name
            if m.tool_calls is not None:
                # Drop tool_call entries whose function.name is empty/missing.
                # These come from truncated streams: when the model hits
                # max_tokens mid-tool-call, the partial delta is still saved
                # to history as `assistant.tool_calls[]`, and replaying it on
                # the next turn makes strict backends (NVIDIA NIM, vLLM)
                # reject the whole request with 400 "Function name was ..."
                # — circuit-breaking the model out of the pool until cooldown.
                clean_tc = []
                for tc in m.tool_calls:
                    fn = (tc or {}).get("function") or {}
                    if (fn.get("name") or "").strip():
                        clean_tc.append(tc)
                if clean_tc:
                    msg_dict["tool_calls"] = clean_tc
            if m.tool_call_id is not None:
                msg_dict["tool_call_id"] = m.tool_call_id
            cleaned_messages.append(msg_dict)

    return system_prompt, cleaned_messages


def _build_openai_response(text: str, model_used: str, provider: str = None, tools=None, tool_calls=None) -> dict:
    """Construye respuesta chat.completion exacta OpenAI."""
    msg = {"role": "assistant", "content": text}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    resp = {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_used,
        "choices": [{
            "index": 0,
            "message": msg,
            "finish_reason": "stop" if not tool_calls else "tool_calls",
            "logprobs": None,
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
    if provider:
        resp["provider"] = provider
    return resp


# =============================================================================
# Virtual Models (optimizados para OpenClaw)
# =============================================================================

VIRTUAL_MODELS = [
    {
        "id": "auto",
        "name": "Wallas AUTO",
        "capabilities": {"chat": True, "vision": True, "tools": True},
        "metadata": {
            "context_window": 200000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": False,
            "input_modalities": ["text", "image", "audio", "pdf"],
            "output_modalities": ["text"],
            "description": "Auto-routing to best available model.",
        }
    },
    {
        "id": "rapido",
        "name": "Wallas RAPIDO",
        "capabilities": {"chat": True, "vision": True},
        "metadata": {
            "context_window": 128000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": False,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "description": "Fastest models (Cerebras, Groq, SambaNova).",
        }
    },
    {
        "id": "standard",
        "name": "Wallas STANDARD",
        "capabilities": {"chat": True, "vision": True, "tools": True},
        "metadata": {
            "context_window": 128000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": False,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "description": "Balanced quality and speed (Gemini Flash, Llama 70B).",
        }
    },
    {
        "id": "razonamiento",
        "name": "Wallas RAZONAMIENTO",
        "capabilities": {"chat": True, "reasoning": True, "vision": True},
        "metadata": {
            "context_window": 64000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": True,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "description": "Chain-of-thought models (DeepSeek R1, Gemini 2.5 Pro).",
        }
    },
    {
        "id": "agentico",
        "name": "Wallas AGENTICO",
        "capabilities": {"chat": True, "tools": True, "vision": True},
        "metadata": {
            "context_window": 128000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": False,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "description": "Reliable multi-step tool callers (Claude Sonnet+, GPT-4o+, Llama 3.3 70B, Mistral Large, DeepSeek V3, Gemini 2.5+). Use for agentic loops where the model must invoke tools several times per turn.",
        }
    },
    {
        "id": "vista",
        "name": "Wallas VISTA",
        "capabilities": {"chat": True, "vision": True},
        "metadata": {
            "context_window": 128000,
            "pricing_tier": "free",
            "supports_tools": True,
            "supports_streaming": True,
            "supports_reasoning_stream": False,
            "input_modalities": ["text", "image"],
            "output_modalities": ["text"],
            "description": "Free vision-capable models (Llama 3.2 Vision, Gemini Flash, Pixtral, Qwen-VL). Use when the request includes images.",
        }
    },
]


# =============================================================================
# Ollama-Compatible Facade (/api/*)
# =============================================================================
try:
    from wallasAPI.ollama_compat import build_ollama_router
except ImportError:
    from .ollama_compat import build_ollama_router  # type: ignore

app.include_router(build_ollama_router(router, VIRTUAL_MODELS))


# =============================================================================
# Health / Status
# =============================================================================

async def _check_camofox_health() -> dict:
    """Check if camofox-browser is running."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:9377/health")
            if r.status_code == 200:
                return {"ok": True, "status": "running", "url": "http://localhost:9377"}
    except Exception:
        pass
    return {"ok": False, "status": "offline", "url": "http://localhost:9377"}


async def _check_mcp_health() -> dict:
    """Check if MCP server is running in HTTP mode."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:8002/sse")
            if r.status_code in (200, 404, 405, 422):  # Any response means server is running
                return {"ok": True, "status": "running", "url": "http://localhost:8002/sse"}
    except Exception:
        pass
    return {"ok": False, "status": "offline", "url": "http://localhost:8002/sse"}


@app.get("/health")
async def health():
    camofox = await _check_camofox_health()
    mcp = await _check_mcp_health()
    return {
        "status": "ok",
        "version": "4.1.0-openclaw",
        "models_loaded": len(MODELS_REGISTRY),
        "auth_mode": "api_key" if _get_proxy_api_key() else "open",
        "services": {
            "wallasapi": {"ok": True, "status": "running", "url": f"http://{HOST}:{PORT}"},
            "camofox_browser": camofox,
            "mcp_server": mcp,
        }
    }


@app.get("/v1/status/services")
async def services_status():
    """Dashboard: estado de todos los servicios WallasAPI."""
    camofox = await _check_camofox_health()
    mcp = await _check_mcp_health()
    return {
        "services": {
            "wallasapi": {"ok": True, "status": "running", "url": f"http://{HOST}:{PORT}", "models_loaded": len(MODELS_REGISTRY)},
            "camofox_browser": camofox,
            "mcp_server": mcp,
        },
        "version": "4.1.0",
        "timestamp": time.time(),
    }


@app.get("/")
async def root():
    return {"service": "WallasAPI-OpenClaw", "docs": "/docs", "version": "4.1.0"}


# =============================================================================
# OpenAI-Compatible: /v1/models
# =============================================================================

@app.get("/v1/models")
async def list_models(
    capability: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("context", regex="^(context|name|provider|latency|none)$"),
    include_dead: bool = Query(False),
):
    """
    OpenAI-compatible model list.
    OpenClaw hace polling a este endpoint frecuentemente.

    Query params:
      capability   — filter by capability (e.g. vision, reasoning)
      provider     — filter by provider id (e.g. nvidia, groq)
      search       — substring match on model id
      sort         — context (default, biggest context first), name, provider, latency, none
      include_dead — set true to include models the probe marked as dead
                     (default: false; dead models are hidden from the listing)
    """
    models_data = []
    for v in VIRTUAL_MODELS:
        entry = {
            "id": v["id"],
            "object": "model",
            "created": 1686935002,
            "owned_by": "wallasapi",
            "context_window": v["metadata"]["context_window"],
            "capabilities": v["capabilities"],
            "metadata": v["metadata"],
            "permission": [{"id": "modelperm-default", "object": "model_permission", "allow_view": True}],
            "root": v["id"],
            "parent": None,
        }
        if capability and capability not in v["capabilities"]:
            continue
        models_data.append(entry)

    for model in MODELS_REGISTRY:
        meta = model.get("metadata", {})
        caps = set(model.get("capabilities", []))
        prov = model.get("provider", "")
        mid = model.get("id", "").lower()

        if capability and capability not in caps:
            continue
        if provider and prov.lower() != provider.lower():
            continue
        if search and search.lower() not in mid:
            continue
        # Hide models the probe confirmed are dead (alive=False), unless
        # the caller explicitly asks for them. alive=None means "not probed
        # yet" and is treated as alive.
        if not include_dead and model.get("alive") is False:
            continue

        # Canonical id is "provider:model" so clients can pin a specific
        # provider when the same publisher-prefixed id (e.g. meta/llama-...)
        # exists under multiple providers. `alt_id` keeps the bare id for
        # legacy clients.
        canonical_id = f"{prov}:{model['id']}" if prov else model["id"]
        entry = {
            "id": canonical_id,
            "alt_id": model["id"],
            "object": "model",
            "created": 1686935002,
            "owned_by": prov,
            "context_window": meta.get("context_window", 128000),
            "capabilities": {
                "completion": True,
                "chat": True,
                "embeddings": "embedding" in caps,
                "reasoning": "reasoning" in caps,
                "vision": "vision" in caps,
                "audio": "audio" in caps,
                "image_generation": "image_gen" in caps,
                "video_generation": "video_gen" in caps,
                "tts": "tts" in caps,
            },
            "metadata": meta,
            "alive": model.get("alive"),
            "last_check": model.get("last_check"),
            "last_latency_ms": model.get("last_latency_ms"),
            "permission": [{"id": "modelperm-default", "object": "model_permission", "allow_view": True}],
            "root": canonical_id,
            "parent": None,
        }
        models_data.append(entry)

    if sort == "context":
        models_data.sort(key=lambda m: m.get("context_window", 0), reverse=True)
    elif sort == "name":
        models_data.sort(key=lambda m: m["id"].lower())
    elif sort == "provider":
        models_data.sort(key=lambda m: (m.get("owned_by", "zzz"), -m.get("context_window", 0)))
    elif sort == "latency":
        models_data.sort(key=lambda m: m.get("metadata", {}).get("last_latency_ms", 99999))
    # sort == "none" keeps insertion order

    return {"object": "list", "data": models_data}


@app.post("/v1/models/verify")
async def verify_models(
    provider: Optional[str] = Query(None, description="Limit probe to a single provider"),
    concurrency: Optional[int] = Query(None, ge=1, le=32, description="Max parallel probes"),
):
    """Trigger a fresh health probe of every chat-capable model.

    Sends a minimal `chat.completions` request to each model and updates
    `alive`, `last_check`, `last_latency_ms`, `last_error` on every entry.
    Persists the registry afterwards.

    Returns a summary: how many were tested, alive, dead, and how long it took.
    """
    result = await verify_models_alive(provider_filter=provider, concurrency=concurrency)
    return result


@app.get("/v1/models/{model_id}")
async def get_model_detail(model_id: str):
    virtual = {v["id"]: v for v in VIRTUAL_MODELS}
    if model_id.lower() in virtual:
        v = virtual[model_id.lower()]
        return {"object": "model", "id": model_id, **v["metadata"]}
    for m in MODELS_REGISTRY:
        if m.get("id") == model_id:
            return {
                "object": "model",
                "id": m["id"],
                "provider": m.get("provider"),
                "capabilities": m.get("capabilities", []),
                "metadata": m.get("metadata", {}),
            }
    raise HTTPException(status_code=404, detail="Model not found")


# =============================================================================
# OpenAI-Compatible: /v1/chat/completions
# =============================================================================

@app.post("/v1/chat/completions", dependencies=[Depends(verify_auth)])
async def chat_completions(
    request: OpenAI_ChatRequest,
    x_willaku_tier: Optional[str] = Header(None, alias="X-Willaku-Tier"),
):
    """
    Endpoint principal para OpenClaw.
    Soporta streaming y non-streaming.

    Routing override: if the `X-Willaku-Tier` header is set to one of
    `auto`, `rapido`, `standard`, `razonamiento`, `agentico`, `vista`, the
    handler ignores `request.model` and routes through that tier instead.
    Lets agentic clients keep their stored model preference while nudging
    strategy per-request (documented in README under "Strategy via header").
    """
    preferred_model = (x_willaku_tier or "").strip() or request.model
    reasoning_mode = preferred_model == "razonamiento"

    system_prompt, cleaned_messages = _normalize_messages_for_openclaw(request.messages)

    if not cleaned_messages:
        raise HTTPException(status_code=400, detail="No user/assistant messages provided")

    last_msg = cleaned_messages[-1]
    user_prompt = last_msg["content"] if last_msg["role"] == "user" else ""
    history = cleaned_messages[:-1]

    # Optional web search enrichment (Gravedad ecosystem)
    use_web_search = getattr(request, 'web_search', False)
    if use_web_search:
        try:
            se = get_search_engine()
            clean_query = extract_clean_search_query(user_prompt)
            log.info(f"[WEB_SEARCH] Query original: '{user_prompt[:60]}...' -> Limpia: '{clean_query}'")
            search_ctx = se.search_and_summarize(clean_query, router, max_results=8)
            system_prompt += f"\n\n[CONTEXTO DE BÚSQUEDA WEB ACTIVADO]\n{search_ctx}\n[FIN CONTEXTO WEB]"
        except Exception as e:
            log.warning(f"[WEB_SEARCH] Falló para chat completions: {e}")

    thread_id = f"oc_{uuid.uuid4().hex[:8]}"

    sanitized_tools = _sanitize_tools(request.tools)

    if request.stream:
        return StreamingResponse(
            _openai_stream_generator(
                system_prompt, user_prompt, preferred_model, thread_id,
                sanitized_tools, request.tool_choice, reasoning_mode, history
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        res, provider, model_used = router.get_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_model=preferred_model,
            tools=sanitized_tools,
            tool_choice=request.tool_choice,
            return_metadata=True,
            reasoning=reasoning_mode,
            history=history,
        )
        return _build_openai_response(res, model_used, provider)


# =============================================================================
# OpenAI-Compatible: /v1/embeddings
# =============================================================================

@app.post("/v1/embeddings", dependencies=[Depends(verify_auth)])
async def embeddings(request: EmbeddingRequest):
    inputs = [request.input] if isinstance(request.input, str) else request.input
    try:
        if hasattr(router, "get_embeddings"):
            data = router.get_embeddings(inputs, model=request.model)
        else:
            data = [[0.0] * 1536 for _ in inputs]
        return {
            "object": "list",
            "data": [{"object": "embedding", "embedding": emb, "index": i} for i, emb in enumerate(data)],
            "model": request.model,
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }
    except Exception as e:
        log.error(f"[EMBED] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# OpenAI-Compatible: /v1/completions (legacy)
# =============================================================================

@app.post("/v1/completions", dependencies=[Depends(verify_auth)])
async def completions(request: CompletionRequest):
    prompt = request.prompt if isinstance(request.prompt, str) else "\n".join(request.prompt)
    chat_req = OpenAI_ChatRequest(
        model=request.model,
        messages=[OpenAI_Message(role="user", content=prompt)],
        stream=request.stream,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    if request.stream:
        return await chat_completions(chat_req)
    else:
        res = await chat_completions(chat_req)
        text = res["choices"][0]["message"]["content"]
        return {
            "id": res["id"],
            "object": "text_completion",
            "created": res["created"],
            "model": res["model"],
            "choices": [{"text": text, "index": 0, "logprobs": None, "finish_reason": "stop"}],
            "usage": res["usage"],
        }


# =============================================================================
# Anthropic-Compatible: /v1/messages (para Claude Code / OpenClaw modo anthropic)
# =============================================================================

@app.post("/v1/messages", dependencies=[Depends(verify_auth)])
async def anthropic_messages(request: Anthropic_Request):
    preferred_model = request.model
    reasoning_mode = preferred_model == "razonamiento"
    system_prompt = request.system or "You are Claude, a helpful assistant."
    last_msg = request.messages[-1]
    user_prompt = last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)
    thread_id = f"anthropic_{uuid.uuid4().hex[:8]}"

    if request.stream:
        return StreamingResponse(
            _anthropic_stream_generator(system_prompt, user_prompt, preferred_model, thread_id, reasoning_mode),
            media_type="text/event-stream",
        )
    else:
        res, provider, model_used = router.get_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_model=preferred_model,
            return_metadata=True,
            reasoning=reasoning_mode,
        )
        return {
            "id": f"msg_{uuid.uuid4()}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": res}],
            "model": model_used,
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }


# =============================================================================
# Streaming Generators (OpenAI SSE)
# =============================================================================

async def _openai_stream_generator(system_prompt, user_prompt, preferred_model, thread_id,
                                     tools=None, tool_choice=None, reasoning=False, history=None):
    chat_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    # Keep-alive inmediato: OpenClaw/Claude Code tienen timeout corto
    yield f"data: {{\"id\": \"{chat_id}\", \"object\": \"chat.completion.chunk\", \"created\": {created_time}, \"model\": \"{preferred_model}\", \"choices\": [{{\"index\": 0, \"delta\": {{\"role\": \"assistant\", \"content\": \"\"}}, \"finish_reason\": null}}]}}\n\n"

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    real_model = preferred_model
    real_provider = None
    saw_tool_call = False

    def run_router():
        try:
            for chunk in router.stream_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                preferred_model=preferred_model,
                thread_id=thread_id,
                tools=tools,
                tool_choice=tool_choice,
                reasoning=reasoning,
                history=history,
            ):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, e)

    threading.Thread(target=run_router, daemon=True).start()

    chunk_count = 0
    while True:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=20.0)
        except asyncio.TimeoutError:
            # SSE comment keep-alive; invisible to client but resets proxies/watchdogs
            yield ": ping\n\n"
            continue

        if chunk is None:
            break
        if isinstance(chunk, Exception):
            raise chunk

        chunk_count += 1
        if chunk["type"] == "metadata":
            # Capture real model and provider from router metadata
            if chunk.get("model"):
                real_model = chunk["model"]
            if chunk.get("provider"):
                real_provider = chunk["provider"]
            continue
        if chunk["type"] == "shim_notice":
            continue

        if chunk["type"] == "content":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": real_model,
                "provider": real_provider,
                "choices": [{"index": 0, "delta": {"content": chunk["chunk"]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(data)}\n\n"

        elif chunk["type"] == "reasoning":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": real_model,
                "provider": real_provider,
                "choices": [{"index": 0, "delta": {"reasoning_content": chunk["chunk"]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(data)}\n\n"

        elif chunk["type"] == "tool_calls":
            # Forward tool_call deltas in OpenAI-compatible shape so agent
            # clients (Hermes, Cursor, Continue) see them. Without this they
            # receive "" content and treat the response as empty.
            saw_tool_call = True
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": real_model,
                "provider": real_provider,
                "choices": [{"index": 0, "delta": {"tool_calls": chunk["chunk"]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(data)}\n\n"

    # If we emitted tool_calls, the finish_reason must be "tool_calls" per
    # the OpenAI spec, not "stop". Clients use this to know they need to
    # execute the tool and send results back.
    finish_reason = "tool_calls" if saw_tool_call else "stop"
    final = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": real_model,
        "provider": real_provider,
        "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
    }
    yield f"data: {json.dumps(final)}\n\n"
    yield "data: [DONE]\n\n"


# =============================================================================
# Streaming Generators (Anthropic SSE)
# =============================================================================

async def _anthropic_stream_generator(system_prompt, user_prompt, preferred_model, thread_id, reasoning=False, history=None):
    msg_id = f"msg_{uuid.uuid4()}"
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': preferred_model, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def run_router():
        try:
            for chunk in router.stream_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                preferred_model=preferred_model,
                thread_id=thread_id,
                reasoning=reasoning,
                history=history,
            ):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, e)

    threading.Thread(target=run_router, daemon=True).start()

    while True:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=20.0)
        except asyncio.TimeoutError:
            yield ": ping\n\n"
            continue

        if chunk is None:
            break
        if isinstance(chunk, Exception):
            raise chunk

        if chunk["type"] == "content":
            data = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": chunk["chunk"]}}
            yield f"event: content_block_delta\ndata: {json.dumps(data)}\n\n"

    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"


# =============================================================================
# Extra endpoints útiles para OpenClaw
# =============================================================================

@app.get("/v1/providers")
async def list_providers():
    """Metadatos de proveedores (útil para debug)."""
    result = []
    for name, cfg in PROVIDERS.items():
        meta = PROVIDER_METADATA.get(name, {})
        result.append({
            "id": name,
            "base_url": cfg.get("base_url"),
            "requires_auth": cfg.get("env_key") is not None,
            "supports_vision": cfg.get("supports_vision", False),
            "supports_streaming": meta.get("supports_streaming", False),
        })
    return {"object": "list", "data": result}


@app.get("/v1/stats")
async def stats():
    """Métricas de circuit breaker y providers en tiempo real."""
    return router.get_circuit_stats()


@app.get("/v1/capabilities/summary")
async def capabilities_summary():
    total = len(MODELS_REGISTRY)
    free = sum(1 for m in MODELS_REGISTRY if m.get("metadata", {}).get("pricing_tier") == "free")
    return {
        "total_models": total,
        "free_models": free,
        "providers": list({m.get("provider") for m in MODELS_REGISTRY}),
        "virtual_models": [v["id"] for v in VIRTUAL_MODELS],
    }


# =============================================================================
# Web Search — Dos backends (DuckDuckGo + Google CSE / SerpAPI fallback)
# =============================================================================

@app.post("/v1/search/web")
async def web_search(request: WebSearchRequest):
    """Búsqueda web con fallback automático entre backends."""
    try:
        se = get_search_engine()
        result = se.search(request.query, max_results=request.max_results, preferred_backend=request.backend)
        return result
    except Exception as e:
        log.error(f"[SEARCH] Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Fork Mode — Ecosistema Gravedad: paralelización multi-provider
# =============================================================================

@app.post("/v1/chat/completions/fork")
async def chat_completions_fork(request: ForkChatRequest):
    """
    Modo Fork: ejecuta múltiples modelos en paralelo para la MISMA tarea
    y devuelve el mejor resultado (o todos si return_all=True).
    """
    system_prompt, cleaned_messages = _normalize_messages_for_openclaw(request.messages)

    if not cleaned_messages:
        raise HTTPException(status_code=400, detail="No user/assistant messages provided")

    last_msg = cleaned_messages[-1]
    user_prompt = last_msg["content"] if last_msg["role"] == "user" else ""

    # Web search opcional
    if request.web_search:
        try:
            se = get_search_engine()
            search_ctx = se.search_and_summarize(user_prompt, router, max_results=8)
            system_prompt += f"\n\n[CONTEXTO DE BÚSQUEDA WEB ACTIVADO]\n{search_ctx}\n[FIN CONTEXTO WEB]"
        except Exception as e:
            log.warning(f"[WEB_SEARCH] Falló en fork: {e}")

    try:
        result = router.fork_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_model=request.model,
            max_parallel=request.max_parallel,
            return_all=request.return_all,
        )

        if request.return_all:
            return {
                "object": "fork_results",
                "model": request.model,
                "results": result,
            }

        # Build OpenAI-compatible response from winner
        others = result.pop("others", [])
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"{result['provider']}/{result['model']}",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": result["text"]},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "fork_metadata": {
                "winner": {
                    "provider": result["provider"],
                    "model": result["model"],
                    "latency_ms": result["latency_ms"],
                    "score": result["score"],
                },
                "others": [
                    {"provider": o["provider"], "model": o["model"], "ok": o["ok"], "latency_ms": o["latency_ms"], "score": o["score"]}
                    for o in others
                ],
                "parallel_count": request.max_parallel,
            }
        }
    except Exception as e:
        log.error(f"[FORK] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Diligence / Compare — Comparar múltiples APIs para una tarea específica
# =============================================================================

@app.post("/v1/diligence/compare")
async def diligence_compare(request: DiligenceCompareRequest):
    """
    Compara en tiempo real qué API cumple mejor una diligencia (tarea específica).
    Ejecuta múltiples modelos en paralelo y devuelve comparación detallada.
    """
    try:
        result = router.fork_completion(
            system_prompt=request.system_prompt,
            user_prompt=request.task,
            max_parallel=request.max_parallel,
            return_all=True,
        )

        # Build comparison report
        ok_results = [r for r in result if r["ok"]]
        fail_results = [r for r in result if not r["ok"]]

        winner = ok_results[0] if ok_results else None

        comparison = {
            "object": "diligence_comparison",
            "task": request.task,
            "criteria": request.criteria,
            "total_attempted": len(result),
            "successful": len(ok_results),
            "failed": len(fail_results),
            "winner": {
                "provider": winner["provider"],
                "model": winner["model"],
                "latency_ms": winner["latency_ms"],
                "score": winner["score"],
                "text_preview": winner["text"][:500] + "..." if len(winner["text"]) > 500 else winner["text"],
            } if winner else None,
            "rankings": [
                {
                    "rank": i + 1,
                    "provider": r["provider"],
                    "model": r["model"],
                    "ok": r["ok"],
                    "latency_ms": r["latency_ms"],
                    "score": r["score"],
                    "error": r.get("error"),
                    "text_preview": r["text"][:300] + "..." if len(r.get("text","")) > 300 else r.get("text",""),
                }
                for i, r in enumerate(result)
            ],
        }
        return comparison

    except Exception as e:
        log.error(f"[DILIGENCE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Browser Automation — Camofox Integration (stealth scraping for Telegram/Gravedad)
# =============================================================================

@app.get("/v1/browser/health")
async def browser_health():
    """Verifica si camofox-browser está corriendo."""
    try:
        client = get_browser_client()
        h = await client.health()
        return h
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/v1/browser/open", dependencies=[Depends(verify_auth)])
async def browser_open(request: BrowserOpenRequest):
    """Abre una URL en camofox y devuelve tabId + snapshot inicial."""
    try:
        client = get_browser_client()
        tab = await client.open_tab(request.url, user_id=request.user_id, session_key=request.session_key)
        tab_id = tab.get("tabId") or tab.get("id")
        snap = await client.snapshot(tab_id, user_id=request.user_id)
        return {
            "status": "ok",
            "tab_id": tab_id,
            "url": request.url,
            "title": snap.get("title", ""),
            "snapshot": snap.get("snapshot", "")[:6000],
        }
    except Exception as e:
        log.error(f"[BROWSER] open error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/browser/act", dependencies=[Depends(verify_auth)])
async def browser_act(request: BrowserActRequest):
    """Ejecuta una acción en un tab existente: snapshot, click, type, scroll, press, screenshot, links, close."""
    try:
        client = get_browser_client()
        action = request.action.lower()

        if action == "snapshot":
            snap = await client.snapshot(request.tab_id, user_id=request.user_id)
            return {"status": "ok", "action": action, "snapshot": snap.get("snapshot", "")[:6000], "title": snap.get("title", "")}

        elif action == "click":
            if not request.ref:
                raise HTTPException(status_code=400, detail="'ref' required for click")
            res = await client.click(request.tab_id, ref=request.ref, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        elif action == "type":
            if not request.ref or request.text is None:
                raise HTTPException(status_code=400, detail="'ref' and 'text' required for type")
            res = await client.type_text(request.tab_id, ref=request.ref, text=request.text, user_id=request.user_id, press_enter=request.press_enter)
            return {"status": "ok", "action": action, "result": res}

        elif action == "scroll":
            res = await client.scroll(request.tab_id, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        elif action == "press":
            if not request.key:
                raise HTTPException(status_code=400, detail="'key' required for press")
            res = await client.press_key(request.tab_id, key=request.key, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        elif action == "screenshot":
            res = await client.screenshot(request.tab_id, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        elif action == "links":
            res = await client.links(request.tab_id, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        elif action == "close":
            res = await client.close_tab(request.tab_id, user_id=request.user_id)
            return {"status": "ok", "action": action, "result": res}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        log.error(f"[BROWSER] act error ({request.action}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/browser/search", dependencies=[Depends(verify_auth)])
async def browser_search(request: BrowserSearchRequest):
    """Ejecuta una búsqueda vía camofox macro (@google_search, @youtube_search, etc.) y extrae snapshots de los top resultados."""
    try:
        from wallasAPI.browser_engine import search_and_browse
        result = await search_and_browse(
            query=request.query,
            user_id=request.user_id,
            macro=request.macro,
            max_results_pages=request.max_results_pages,
        )
        return result
    except Exception as e:
        log.error(f"[BROWSER] search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/browser/summarize", dependencies=[Depends(verify_auth)])
async def browser_summarize(request: BrowserOpenRequest):
    """Abre URL, extrae snapshot legible, cierra tab — devuelve contenido listo para pasar al LLM."""
    try:
        from wallasAPI.browser_engine import browse_and_summarize
        result = await browse_and_summarize(request.url, user_id=request.user_id)
        return result
    except Exception as e:
        log.error(f"[BROWSER] summarize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/browser/youtube/transcript")
async def browser_youtube_transcript(request: YouTubeTranscriptRequest):
    """Extrae transcript de YouTube vía camofox (usa yt-dlp si está disponible)."""
    try:
        client = get_browser_client()
        result = await client.youtube_transcript(request.url, languages=request.languages)
        return result
    except Exception as e:
        log.error(f"[BROWSER] youtube transcript error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  WallasAPI-OpenClaw Edition v4.0")
    print("  Optimizado para OpenClaw / Claude Code / IDEs")
    print(f"  Endpoint OpenAI: http://{HOST}:{PORT}/v1")
    print(f"  Endpoint Ollama: http://{HOST}:{PORT}/api")
    print(f"  Health Check:    http://{HOST}:{PORT}/health")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning" if SILENT_AGENT_LOGS else "info")
