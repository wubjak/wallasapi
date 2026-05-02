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
# PATH RESOLUTION: Si estás al lado del wallasAPI original, úsalo.
# Si no, usa el router embebido (más abajo).
# =============================================================================
_WALLAS_ORIGINAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wallasAPI")
if os.path.isdir(_WALLAS_ORIGINAL) and os.path.isfile(os.path.join(_WALLAS_ORIGINAL, "router.py")):
    sys.path.insert(0, os.path.dirname(_WALLAS_ORIGINAL))
    from wallasAPI.router import AIRouter
    from wallasAPI.config import MODELS_REGISTRY, PROVIDERS, PROVIDER_METADATA, PROXY_API_KEY_ENV
    from wallasAPI.model_fetcher import update_registry_async, load_registry_from_cache
    from wallasAPI.search_engine import get_search_engine
    from wallasAPI.logger import log
    _HAS_ORIGINAL = True
else:
    _HAS_ORIGINAL = False
    # Fallback: implementación mínima embebida (solo para demo/standalone)
    from .router_embedded import AIRouter
    from .config_embedded import MODELS_REGISTRY, PROVIDERS, PROVIDER_METADATA, PROXY_API_KEY_ENV
    from .model_fetcher_embedded import update_registry_async, load_registry_from_cache
    from .logger_embedded import log

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
    yield
    log.info("[SHUTDOWN] WallasAPI-OpenClaw detenido.")


app = FastAPI(
    title="WallasAPI-OpenClaw",
    description="Multi-provider AI router optimized for OpenClaw. OpenAI-compatible gateway.",
    version="4.0.0-openclaw",
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


# =============================================================================
# Helpers
# =============================================================================

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
            cleaned_messages.append({
                "role": m.role,
                "content": m.content if isinstance(m.content, str) else str(m.content),
                "name": m.name,
                "tool_calls": m.tool_calls,
                "tool_call_id": m.tool_call_id,
            })

    return system_prompt, cleaned_messages


def _build_openai_response(text: str, model_used: str, tools=None, tool_calls=None) -> dict:
    """Construye respuesta chat.completion exacta OpenAI."""
    msg = {"role": "assistant", "content": text}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {
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
]


# =============================================================================
# Health / Status
# =============================================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "4.0.0-openclaw",
        "models_loaded": len(MODELS_REGISTRY),
        "auth_mode": "api_key" if _get_proxy_api_key() else "open",
        "openclaw_ready": True,
        "endpoints": {
            "openai": "/v1/chat/completions",
            "models": "/v1/models",
            "anthropic": "/v1/messages",
        }
    }


@app.get("/")
async def root():
    return {"service": "WallasAPI-OpenClaw", "docs": "/docs", "version": "4.0.0"}


# =============================================================================
# OpenAI-Compatible: /v1/models
# =============================================================================

@app.get("/v1/models")
async def list_models(
    capability: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    OpenAI-compatible model list.
    OpenClaw hace polling a este endpoint frecuentemente.
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

        entry = {
            "id": model["id"],
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
            "permission": [{"id": "modelperm-default", "object": "model_permission", "allow_view": True}],
            "root": model["id"],
            "parent": None,
        }
        models_data.append(entry)

    return {"object": "list", "data": models_data}


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
async def chat_completions(request: OpenAI_ChatRequest):
    """
    Endpoint principal para OpenClaw.
    Soporta streaming y non-streaming.
    """
    preferred_model = request.model
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
            search_ctx = se.search_and_summarize(user_prompt, router, max_results=8)
            system_prompt += f"\n\n[CONTEXTO DE BÚSQUEDA WEB ACTIVADO]\n{search_ctx}\n[FIN CONTEXTO WEB]"
        except Exception as e:
            log.warning(f"[WEB_SEARCH] Falló para chat completions: {e}")

    thread_id = f"oc_{uuid.uuid4().hex[:8]}"

    if request.stream:
        return StreamingResponse(
            _openai_stream_generator(
                system_prompt, user_prompt, preferred_model, thread_id,
                request.tools, request.tool_choice, reasoning_mode, history
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
            tools=request.tools,
            tool_choice=request.tool_choice,
            return_metadata=True,
            reasoning=reasoning_mode,
            history=history,
        )
        return _build_openai_response(res, model_used)


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
            continue
        if chunk["type"] == "shim_notice":
            continue

        if chunk["type"] == "content":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": preferred_model,
                "choices": [{"index": 0, "delta": {"content": chunk["chunk"]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(data)}\n\n"

        elif chunk["type"] == "reasoning":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": preferred_model,
                "choices": [{"index": 0, "delta": {"reasoning_content": chunk["chunk"]}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(data)}\n\n"

    final = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": preferred_model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
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
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  WallasAPI-OpenClaw Edition v4.0")
    print("  Optimizado para OpenClaw / Claude Code / IDEs")
    print(f"  Endpoint OpenAI: http://{HOST}:{PORT}/v1")
    print(f"  Health Check:    http://{HOST}:{PORT}/health")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning" if SILENT_AGENT_LOGS else "info")
