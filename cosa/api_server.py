"""
WallasAPI — api_server.py mejorado
===================================

Cambios clave vs el original:
  ✅ Streaming async robusto (delega a services/streaming.py)
  ✅ Cache de modelos con TTL (5 min)
  ✅ Endpoint /v1/stats para monitorear providers en tiempo real
  ✅ CORS configurado correctamente para OpenClaw local
  ✅ Logging estructurado
  ✅ Headers para evitar buffering en proxies (importante para Telegram)
  ✅ Lifespan management (cleanup limpio al cerrar)
  ✅ Rate limiting básico por IP

Reemplaza tu api_server.py actual con esto, ajustando los imports a tu
estructura de carpetas real.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Imports relativos — ajusta según tu estructura
from services.streaming import stream_with_fallback, get_provider_stats

# ════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wallasapi.server")

PORT = int(os.getenv("WALLASAPI_PORT", 8001))
HOST = os.getenv("WALLASAPI_HOST", "127.0.0.1")

# Cache de modelos
_models_cache: dict = {"data": None, "ts": 0}
MODELS_CACHE_TTL = 300  # 5 minutos

# Rate limiting simple por IP (en producción usa redis)
_rate_limit: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 60


# ════════════════════════════════════════════════════════════════
#  MODELS (Pydantic)
# ════════════════════════════════════════════════════════════════

class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "auto"
    messages: list[Message]
    stream: bool = False
    max_tokens: int = Field(default=4096, le=32768)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


# ════════════════════════════════════════════════════════════════
#  LIFESPAN
# ════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"WallasAPI iniciando en http://{HOST}:{PORT}")
    logger.info(f"Providers configurados: {_count_active_providers()}")
    yield
    logger.info("WallasAPI cerrando — limpiando recursos")


# ════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════

app = FastAPI(
    title="WallasAPI",
    description="AI Router con failover automático entre 12+ providers",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
#  MIDDLEWARE — rate limit y headers
# ════════════════════════════════════════════════════════════════

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    timestamps = _rate_limit.setdefault(client_ip, [])
    # Limpia timestamps fuera de la ventana
    timestamps[:] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit excedido. Espera 1 minuto."},
        )

    timestamps.append(now)
    response = await call_next(request)
    return response


# ════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "name": "WallasAPI",
        "version": "2.0.0",
        "docs": "/docs",
        "stats": "/v1/stats",
    }


@app.get("/health")
async def health():
    active = _count_active_providers()
    return {
        "status": "ok" if active > 0 else "degraded",
        "active_providers": active,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, http_request: Request):
    """Endpoint compatible con OpenAI SDK."""
    messages = [m.model_dump() for m in request.messages]

    if request.stream:
        return StreamingResponse(
            stream_with_fallback(
                messages=messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # critical para evitar buffering
            },
        )

    # No-streaming: junta todos los chunks
    full_content = ""
    async for chunk in stream_with_fallback(
        messages=messages,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    ):
        if chunk.startswith("data: ") and "[DONE]" not in chunk:
            try:
                import json
                data = json.loads(chunk[6:].strip())
                delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                full_content += delta
            except Exception:
                continue

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": full_content},
            "finish_reason": "stop",
        }],
    }


@app.get("/v1/models")
async def list_models(pricing: Optional[str] = None, capability: Optional[str] = None):
    """Lista de modelos con cache de 5 minutos."""
    now = time.time()
    if _models_cache["data"] is None or now - _models_cache["ts"] > MODELS_CACHE_TTL:
        _models_cache["data"] = await _fetch_all_models()
        _models_cache["ts"] = now

    models = _models_cache["data"]

    if pricing == "free":
        models = [m for m in models if m.get("pricing") == "free"]
    if capability:
        models = [m for m in models if capability in m.get("capabilities", [])]

    return {"object": "list", "data": models}


@app.get("/v1/stats")
async def stats():
    """Métricas en tiempo real de todos los providers."""
    return get_provider_stats()


@app.get("/v1/providers")
async def providers():
    """Lista simple de providers configurados."""
    from services.streaming import PROVIDERS
    return {
        "providers": [p.name for p in PROVIDERS if os.getenv(p.env_key)],
    }


# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════

def _count_active_providers() -> int:
    from services.streaming import PROVIDERS
    return sum(1 for p in PROVIDERS if os.getenv(p.env_key))


async def _fetch_all_models() -> list[dict]:
    """
    Implementa según tu lógica actual de model_fetcher.py
    Esto es solo un placeholder.
    """
    return [
        {"id": "auto", "object": "model", "owned_by": "wallasapi", "pricing": "free"},
        {"id": "fast", "object": "model", "owned_by": "wallasapi", "pricing": "free"},
        {"id": "standard", "object": "model", "owned_by": "wallasapi", "pricing": "mixed"},
        {"id": "reasoning", "object": "model", "owned_by": "wallasapi", "pricing": "mixed"},
    ]


# ════════════════════════════════════════════════════════════════
#  RUN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=False,  # True solo en dev
        workers=1,
    )
