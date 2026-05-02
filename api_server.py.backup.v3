# wallasAPI/api_server.py
"""
WallasAPI — El Enrutador de IA Definitivo (Powered by ProyectoIG).
Exposes OpenAI and Anthropic-compatible endpoints backed by the AI Router.
Supports both open local mode and API key authentication for VPS deployment.
"""
import os
import time
import uuid
import json
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Union

from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .router import AIRouter
from .config import MODELS_REGISTRY, PROXY_API_KEY_ENV, PROVIDERS, PROVIDER_METADATA
from .model_fetcher import update_registry_async
from .logger import log
from .banner import show_banner

# Load .env if not already loaded
from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model registry on startup."""
    log.info("[STARTUP] Iniciando Universal AI Services Proxy...")
    
    from .model_fetcher import load_registry_from_cache
    has_cache = load_registry_from_cache()
    
    if has_cache:
        log.info(f"[READY] WallasAPI iniciado con caché. {len(MODELS_REGISTRY)} modelos disponibles.")
        # Background update to keep registry fresh
        asyncio.create_task(update_registry_async())
    else:
        log.info("[FETCH] Sin caché. Descargando modelos por primera vez (esto puede tardar)...")
        await update_registry_async()
        log.info(f"[READY] Servidor listo. {len(MODELS_REGISTRY)} modelos cargados.")
        
    yield
    log.info("[SHUTDOWN] Servidor detenido.")


app = FastAPI(
    title="WallasAPI — El Enrutador de IA Definitivo",
    description="Multi-provider AI proxy with OpenAI and Anthropic compatibility for Legalia OS and external IDEs.",
    version="3.1.0",
    lifespan=lifespan,
)

# CORS — Allow all origins for local dev; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = AIRouter()


# ============================================================================
# Authentication
# ============================================================================

def _get_proxy_api_key() -> Optional[str]:
    """Returns the configured proxy API key, or None if open mode."""
    return os.getenv(PROXY_API_KEY_ENV)


async def verify_auth(authorization: Optional[str] = Header(None)):
    """
    Dependency that checks the Authorization header against the configured
    PROXY_API_KEY. If no key is configured, the proxy runs in open mode.
    """
    expected_key = _get_proxy_api_key()
    if not expected_key:
        return  # Open mode — no auth required

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Accept "Bearer <key>" or just "<key>"
    token = authorization.replace("Bearer ", "").strip()
    if token != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


# ============================================================================
# Request Models (Pydantic)
# ============================================================================

class OpenAI_Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class OpenAI_ChatRequest(BaseModel):
    model: str
    messages: List[OpenAI_Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


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


class ObsidianSyncRequest(BaseModel):
    thread_id: str
    message_index: Optional[int] = None
    full_chat: Optional[bool] = False


class OCRRequest(BaseModel):
    file_data: str
    mime_type: str
    engine: str = "local"


class InterpretRequest(BaseModel):
    image_data: str
    model: Optional[str] = None


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "text-embedding-3-small"


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "models_loaded": len(MODELS_REGISTRY),
        "auth_mode": "api_key" if _get_proxy_api_key() else "open",
        "version": "2.0.0",
    }


# ============================================================================
# OpenAI-Compatible Endpoints
# ============================================================================

@app.get("/v1/models")
async def list_models(
    capability: Optional[str] = Query(None, description="Filter by capability (e.g. vision, reasoning, free, audio, file)"),
    provider: Optional[str] = Query(None, description="Filter by provider name (e.g. gemini, groq, openrouter)"),
    pricing: Optional[str] = Query(None, description="Filter by pricing tier: free, paid, mixed"),
    search: Optional[str] = Query(None, description="Search by model ID substring"),
    modality: Optional[str] = Query(None, description="Filter by input/output modality: text, image, audio, video, pdf"),
):
    """
    OpenAI-compatible enriched model list.
    Clients (IDEs, apps) can filter by capability, provider, pricing, etc.
    Every entry includes rich metadata: context_window, max_images, tool support,
    streaming support, pricing tier, and supported modalities.
    """
    virtual_models = [
        {
            "id": "auto",
            "name": "🤖 Wallas AUTO (Inteligente)",
            "capabilities": {"chat": True},
            "metadata": {
                "context_window": 200000,
                "pricing_tier": "mixed",
                "supports_tools": True,
                "supports_streaming": True,
                "supports_reasoning_stream": False,
                "input_modalities": ["text", "image", "audio", "pdf"],
                "output_modalities": ["text"],
                "description": "Automatically picks the best available model based on your request.",
            }
        },
        {
            "id": "rapido",
            "name": "⚡ Wallas RÁPIDO (Velocidad)",
            "capabilities": {"chat": True},
            "metadata": {
                "context_window": 128000,
                "pricing_tier": "free",
                "supports_tools": True,
                "supports_streaming": True,
                "supports_reasoning_stream": False,
                "input_modalities": ["text", "image"],
                "output_modalities": ["text"],
                "description": "Prioritizes the fastest models (Cerebras, Groq, SambaNova).",
            }
        },
        {
            "id": "standard",
            "name": "⚖️ Wallas STANDARD (Equilibrado)",
            "capabilities": {"chat": True},
            "metadata": {
                "context_window": 128000,
                "pricing_tier": "free",
                "supports_tools": True,
                "supports_streaming": True,
                "supports_reasoning_stream": False,
                "input_modalities": ["text", "image"],
                "output_modalities": ["text"],
                "description": "Balanced quality and speed (Gemini Flash, Llama 70B, GPT-4o).",
            }
        },
        {
            "id": "razonamiento",
            "name": "🧠 Wallas RAZONAMIENTO (Pensar)",
            "capabilities": {"reasoning": True, "chat": True},
            "metadata": {
                "context_window": 64000,
                "pricing_tier": "free",
                "supports_tools": True,
                "supports_streaming": True,
                "supports_reasoning_stream": True,
                "input_modalities": ["text", "image"],
                "output_modalities": ["text"],
                "description": "Chain-of-thought models (DeepSeek R1, Gemini 2.5 Pro, o1).",
            }
        }
    ]

    models_data = []
    for v in virtual_models:
        entry = {
            "id": v["id"],
            "object": "model",
            "created": 1686935002,
            "owned_by": "wallasapi",
            "context_window": v["metadata"]["context_window"],
            "capabilities": v["capabilities"],
            "metadata": v["metadata"],
            "permission": [{"id": "modelperm-default", "object": "model_permission", "allow_view": True}]
        }
        # Apply filters to virtual models
        if capability and capability not in v["capabilities"] and capability not in v["metadata"].get("input_modalities", []):
            continue
        if pricing and v["metadata"].get("pricing_tier") != pricing:
            continue
        models_data.append(entry)

    for model in MODELS_REGISTRY:
        meta = model.get("metadata", {})
        caps = set(model.get("capabilities", []))
        prov = model.get("provider", "")
        mid = model.get("id", "").lower()

        # Filters
        if capability and capability not in caps and capability not in meta.get("input_modalities", []):
            continue
        if provider and prov.lower() != provider.lower():
            continue
        if pricing and meta.get("pricing_tier") != pricing:
            continue
        if search and search.lower() not in mid:
            continue
        if modality and modality not in meta.get("input_modalities", []) and modality not in meta.get("output_modalities", []):
            continue

        # Build OpenAI-compatible enriched entry
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
            "permission": [{
                "id": "modelperm-default",
                "object": "model_permission",
                "created": 1686935002,
                "allow_create_engine": False,
                "allow_sampling": True,
                "allow_logprobs": True,
                "allow_search_indices": False,
                "allow_view": True,
                "allow_fine_tuning": False,
                "organization": "*",
                "group": None,
                "is_blocking": False
            }],
            "root": model["id"],
            "parent": None
        }
        models_data.append(entry)

    return {"object": "list", "data": models_data}


@app.get("/v1/models/{model_id}")
async def get_model_detail(model_id: str):
    """Returns full metadata for a single model, including provider limits."""
    # Check virtual models first
    virtual = {
        "auto": {"name": "Wallas AUTO", "description": "Auto-routing"},
        "rapido": {"name": "Wallas RÁPIDO", "description": "Speed priority"},
        "standard": {"name": "Wallas STANDARD", "description": "Balanced"},
        "razonamiento": {"name": "Wallas RAZONAMIENTO", "description": "Reasoning priority"},
    }
    if model_id.lower() in virtual:
        return {"object": "model", "id": model_id, **virtual[model_id.lower()]}

    for model in MODELS_REGISTRY:
        if model.get("id") == model_id:
            return {
                "object": "model",
                "id": model["id"],
                "provider": model.get("provider"),
                "capabilities": model.get("capabilities", []),
                "meta": model.get("meta", {}),
                "metadata": model.get("metadata", {}),
                "desc": model.get("desc", ""),
            }
    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/v1/registry", dependencies=[Depends(verify_auth)])
async def get_full_registry():
    """Returns the full model registry with capabilities and metadata."""
    return {"object": "list", "data": MODELS_REGISTRY}


@app.get("/v1/capabilities/summary")
async def capabilities_summary():
    """
    Aggregate summary of all available capabilities across the registry.
    Useful for clients to build capability-aware UIs.
    """
    total = len(MODELS_REGISTRY)
    free_count = 0
    paid_count = 0
    vision_count = 0
    audio_count = 0
    reasoning_count = 0
    tool_count = 0
    streaming_count = 0
    image_gen_count = 0
    video_gen_count = 0
    file_native_count = 0
    providers_seen = set()
    models_by_provider: Dict[str, int] = {}

    for m in MODELS_REGISTRY:
        caps = set(m.get("capabilities", []))
        meta = m.get("metadata", {})
        prov = m.get("provider", "unknown")

        providers_seen.add(prov)
        models_by_provider[prov] = models_by_provider.get(prov, 0) + 1

        if meta.get("pricing_tier") == "free":
            free_count += 1
        elif meta.get("pricing_tier") == "paid":
            paid_count += 1

        if "vision" in caps:
            vision_count += 1
        if "audio" in caps:
            audio_count += 1
        if "reasoning" in caps:
            reasoning_count += 1
        if meta.get("supports_tools"):
            tool_count += 1
        if meta.get("supports_streaming"):
            streaming_count += 1
        if "image_gen" in caps:
            image_gen_count += 1
        if "video_gen" in caps:
            video_gen_count += 1
        if "file" in caps:
            file_native_count += 1

    return {
        "total_models": total,
        "providers": list(providers_seen),
        "models_by_provider": models_by_provider,
        "pricing": {"free": free_count, "paid": paid_count, "mixed": total - free_count - paid_count},
        "capabilities": {
            "vision": vision_count,
            "audio": audio_count,
            "reasoning": reasoning_count,
            "tools": tool_count,
            "streaming": streaming_count,
            "image_generation": image_gen_count,
            "video_generation": video_gen_count,
            "native_file_support": file_native_count,
        },
        "virtual_models": ["auto", "rapido", "standard", "razonamiento"],
    }


@app.get("/v1/providers")
async def list_providers():
    """
    Returns provider-level metadata: what each provider supports globally,
    auth requirements, and operational limits. Clients use this to decide
    how to format requests (e.g. native files vs text shim).
    """
    result = []
    for name, cfg in PROVIDERS.items():
        meta = PROVIDER_METADATA.get(name, {})
        result.append({
            "id": name,
            "base_url": cfg.get("base_url"),
            "requires_auth": cfg.get("env_key") is not None,
            "auth_env_key": cfg.get("env_key"),
            "supports_vision": cfg.get("supports_vision", False),
            "supports_audio": cfg.get("supports_audio", False),
            "supports_native_files": cfg.get("supports_files_native", False),
            "max_images_per_request": meta.get("max_images_per_request"),
            "supports_tools": meta.get("supports_tools", False),
            "supports_streaming": meta.get("supports_streaming", False),
            "supports_reasoning_stream": meta.get("supports_reasoning_stream", False),
            "max_context_hint": meta.get("max_context_hint"),
            "pricing": meta.get("pricing", "unknown"),
            "input_modalities": meta.get("input_modalities", ["text"]),
            "output_modalities": meta.get("output_modalities", ["text"]),
            "speed_priority": cfg.get("speed_rank", None),
        })
    return {"object": "list", "data": result}


@app.get("/v1/threads", dependencies=[Depends(verify_auth)])
async def list_threads():
    """Returns a list of all saved conversation threads with titles."""
    from .memory import MemoryManager
    threads = MemoryManager.list_threads()
    return {"object": "list", "data": threads}


@app.post("/v1/chat/completions", dependencies=[Depends(verify_auth)])
async def chat_completions(
    request: OpenAI_ChatRequest,
    x_willaku_tier: Optional[str] = Header(None),
    x_willaku_model: Optional[str] = Header(None),
):
    """OpenAI format: Chat completions (streaming and non-streaming)."""
    # Use header overrides if present
    # Normalización WallasAI: traduciendo tiers antiguos a categorías maestras
    if x_willaku_tier == "reasoning": x_willaku_tier = "razonamiento"
    if x_willaku_tier == "fast": x_willaku_tier = "rapido"

    preferred_model = x_willaku_model or request.model
    # Si el modelo solicitado es una categoría, lo usamos como base
    reasoning_mode = (x_willaku_tier == "razonamiento" or preferred_model == "razonamiento")

    # Extract system prompt from messages
    system_prompt = "You are a helpful assistant."
    cleaned_messages = []
    
    # GUARDAR PARA INSPECCIÓN (DEBUG)
    try:
        req_json = request.model_dump()
        with open(os.path.join(os.path.dirname(__file__), "last_request.json"), "w", encoding="utf-8") as f:
            json.dump(req_json, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.warning(f"No se pudo guardar last_request.json: {e}")
        
    for m in request.messages:
        if m.role == "system":
            system_prompt = m.content if isinstance(m.content, str) else str(m.content)
        else:
            cleaned_messages.append({"role": m.role, "content": m.content})

    if not cleaned_messages:
        raise HTTPException(status_code=400, detail="No user messages provided")

    last_user_msg = cleaned_messages[-1]["content"]
    user_prompt = last_user_msg if isinstance(last_user_msg, str) else str(last_user_msg)

    thread_id = f"proxy_{uuid.uuid4().hex[:8]}"
    
    # DEBUG: Inspeccionar qué está mandando OpenClaude
    prompt_len = len(user_prompt)
    if prompt_len > 10000:
        log.info(f"[DEBUG] Prompt detectado de {prompt_len} chars. Contenido inicial: {user_prompt[:500]}...")

    if request.stream:
        return StreamingResponse(
            _openai_stream_generator(system_prompt, user_prompt, preferred_model, thread_id, request.tools, request.tool_choice, reasoning_mode, history=cleaned_messages[:-1]),
            media_type="text/event-stream",
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
            history=cleaned_messages[:-1]
        )
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_used,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": res},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }


@app.post("/v1/embeddings", dependencies=[Depends(verify_auth)])
async def embeddings(request: EmbeddingRequest):
    """OpenAI format: Embeddings endpoint."""
    inputs = [request.input] if isinstance(request.input, str) else request.input
    
    # Simple proxy to router or internal method
    # For now, let's try to use the router's embedding capability if it exists
    # If not, we'll return a dummy or use a default provider
    try:
        # Check if router has an embed method (we should add one if not)
        if hasattr(router, "get_embeddings"):
            data = router.get_embeddings(inputs, model=request.model)
        else:
            # Fallback or error
            log.warning(f"[EMBED] Router doesn't have get_embeddings. Returning dummy.")
            data = [[0.0] * 1536 for _ in inputs]
            
        return {
            "object": "list",
            "data": [
                {"object": "embedding", "embedding": emb, "index": i}
                for i, emb in enumerate(data)
            ],
            "model": request.model,
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        }
    except Exception as e:
        log.error(f"[EMBED] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions", dependencies=[Depends(verify_auth)])
async def completions(request: CompletionRequest):
    """OpenAI format: Legacy completions endpoint (proxied to chat)."""
    # Many old tools still use this. We map it to a single user message.
    prompt = request.prompt if isinstance(request.prompt, str) else "\n".join(request.prompt)
    
    chat_request = OpenAI_ChatRequest(
        model=request.model,
        messages=[OpenAI_Message(role="user", content=prompt)],
        stream=request.stream,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    if request.stream:
        return await chat_completions(chat_request)
    else:
        res = await chat_completions(chat_request)
        # Adapt chat response to completion response
        return {
            "id": res["id"],
            "object": "text_completion",
            "created": res["created"],
            "model": res["model"],
            "choices": [{
                "text": res["choices"][0]["message"]["content"],
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            "usage": res["usage"]
        }


# ============================================================================
# Anthropic-Compatible Endpoints
# ============================================================================

@app.post("/v1/messages", dependencies=[Depends(verify_auth)])
async def anthropic_messages(
    request: Anthropic_Request,
    x_willaku_tier: Optional[str] = Header(None),
    x_willaku_model: Optional[str] = Header(None),
):
    """Anthropic format: Messages endpoint (Claude Code compatibility)."""
    # Normalización WallasAI: traduciendo tiers antiguos a categorías maestras
    if x_willaku_tier == "reasoning": x_willaku_tier = "razonamiento"
    if x_willaku_tier == "fast": x_willaku_tier = "rapido"

    # Use header overrides
    preferred_model = x_willaku_model or request.model
    reasoning_mode = (x_willaku_tier == "razonamiento" or preferred_model == "razonamiento")

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


# ============================================================================
# Streaming Generators
# ============================================================================

async def _openai_stream_generator(system_prompt, user_prompt, preferred_model, thread_id, tools=None, tool_choice=None, reasoning=False, history=None):
    """Generates SSE chunks in OpenAI format."""
    chat_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    chunk_count = 0
    # Keep-alive: send initial token immediately to prevent client timeout
    yield "data: {\"id\": \"chatcmpl-init\", \"object\": \"chat.completion.chunk\", \"created\": " + str(created_time) + ", \"model\": \"" + preferred_model + "\", \"choices\": [{\"index\": 0, \"delta\": {\"role\": \"assistant\", \"content\": \"\"}, \"finish_reason\": null}]}\n\n"
    
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
        chunk_count += 1
        if chunk_count % 10 == 0:
            log.info(f"[STREAM] Enviando chunk {chunk_count} al cliente.")
        if chunk["type"] == "metadata":
            continue  # Not part of OpenAI spec

        if chunk["type"] == "shim_notice":
            continue  # Internal notification, not for external clients

        if chunk["type"] == "content":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": preferred_model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": chunk["chunk"]},
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(data)}\n\n"

        elif chunk["type"] == "reasoning":
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": preferred_model,
                "choices": [{
                    "index": 0,
                    "delta": {"reasoning_content": chunk["chunk"]},
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(data)}\n\n"

    # Termination
    final = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": preferred_model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final)}\n\n"
    yield "data: [DONE]\n\n"


async def _anthropic_stream_generator(system_prompt, user_prompt, preferred_model, thread_id, reasoning=False, history=None):
    """Generates SSE chunks in Anthropic format."""
    msg_id = f"msg_{uuid.uuid4()}"

    # Message start
    yield (
        f"event: message_start\n"
        f"data: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': preferred_model, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
    )
    yield (
        f"event: content_block_start\n"
        f"data: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
    )

    for chunk in router.stream_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        preferred_model=preferred_model,
        thread_id=thread_id,
        reasoning=reasoning,
        history=history,
    ):
        if chunk["type"] == "content":
            data = {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": chunk["chunk"]},
            }
            yield f"event: content_block_delta\ndata: {json.dumps(data)}\n\n"

    # Termination events
    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"


# ============================================================================
# Gravedad Premium Endpoints
# ============================================================================

@app.post("/v1/obsidian/sync", dependencies=[Depends(verify_auth)])
async def sync_to_obsidian(request: ObsidianSyncRequest):
    """Manually sync a message or chat to Obsidian."""
    from .memory import MemoryManager
    mem = MemoryManager(request.thread_id)
    success = mem.sync_to_obsidian(
        message_index=request.message_index,
        full_chat=request.full_chat
    )
    if success:
        return {"status": "success", "message": "Sincronizado con Obsidian"}
    else:
        raise HTTPException(status_code=500, detail="Error sincronizando con Obsidian")


@app.post("/v1/ocr/process", dependencies=[Depends(verify_auth)])
async def process_ocr(request: OCRRequest):
    """Process a file using OCR."""
    from .file_utils import FileProcessor
    res = FileProcessor.extract_text(
        request.file_data, 
        request.mime_type, 
        ocr_engine=request.engine
    )
    return res


@app.post("/v1/interpret", dependencies=[Depends(verify_auth)])
async def interpret_image(request: InterpretRequest):
    """Analyze an image and return its text description."""
    description = router.interpret_image(request.image_data, preferred_model=request.model)
    return {"description": description}


# ============================================================================
# Direct Execution
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    show_banner()
    # Change port to 8001 to avoid conflict with ai_services
    log.info("[BOOT] Iniciando WallasAPI en el puerto 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
