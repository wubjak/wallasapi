"""
Ollama-compatible facade for WallasAPI.

Exposes /api/version, /api/tags, /api/show, /api/generate, /api/chat
on the same FastAPI app as the OpenAI-compatible endpoints, so that any
Ollama client pointed at http://<host>:<port> sees the union of:

  - WallasAPI cloud models (MODELS_REGISTRY + VIRTUAL_MODELS), and
  - Real Ollama models from the local daemon at OLLAMA_UPSTREAM
    (default http://localhost:11434), proxied transparently.

Cloud-model traffic is delegated to AIRouter; Ollama-tagged traffic is
forwarded byte-for-byte to the upstream daemon.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

try:
    from wallasAPI.config import MODELS_REGISTRY
    from wallasAPI.logger import log
except ImportError:
    from .config import MODELS_REGISTRY  # type: ignore
    from .logger import log  # type: ignore


OLLAMA_UPSTREAM = os.getenv("OLLAMA_UPSTREAM", "http://localhost:11434").rstrip("/")
OLLAMA_VERSION_STRING = os.getenv("WALLAS_OLLAMA_VERSION", "0.1.0-wallas")
_TAG_CACHE_TTL = 30.0
_UPSTREAM_TIMEOUT = 1.5

_tag_cache: Dict[str, Any] = {"at": 0.0, "models": []}


# ---------------------------------------------------------------------------
# Pydantic request bodies
# ---------------------------------------------------------------------------

class OllamaShowRequest(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None


class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str = ""
    system: Optional[str] = None
    stream: Optional[bool] = True
    options: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    keep_alive: Optional[Any] = None
    raw: Optional[bool] = None
    format: Optional[Any] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None


class OllamaChatMessage(BaseModel):
    role: str
    content: str = ""
    images: Optional[List[str]] = None


class OllamaChatRequest(BaseModel):
    model: str
    messages: List[OllamaChatMessage]
    stream: Optional[bool] = True
    options: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    format: Optional[Any] = None
    keep_alive: Optional[Any] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest_for(name: str) -> str:
    return "sha256:" + hashlib.sha256(name.encode("utf-8")).hexdigest()


def _wallas_models_as_ollama_tags(virtual_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tags: List[Dict[str, Any]] = []
    seen: set = set()

    for v in virtual_models:
        vid = v["id"]
        if vid in seen:
            continue
        seen.add(vid)
        meta = v.get("metadata", {})
        tags.append({
            "name": vid,
            "model": vid,
            "modified_at": "2026-01-01T00:00:00Z",
            "size": 0,
            "digest": _digest_for(vid),
            "details": {
                "parent_model": "",
                "format": "cloud",
                "family": "wallas-virtual",
                "families": ["wallas-virtual"],
                "parameter_size": str(meta.get("context_window", 0)),
                "quantization_level": "none",
            },
        })

    # Sort cloud models by context_window descending so the most capable
    # appear first in Ollama clients. Virtual models stay on top.
    cloud_models = sorted(
        MODELS_REGISTRY,
        key=lambda m: m.get("metadata", {}).get("context_window", 0),
        reverse=True,
    )

    for m in cloud_models:
        mid = m.get("id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        provider = m.get("provider", "wallas") or "wallas"
        meta = m.get("metadata", {})
        tags.append({
            "name": mid,
            "model": mid,
            "modified_at": "2026-01-01T00:00:00Z",
            "size": 0,
            "digest": _digest_for(mid),
            "details": {
                "parent_model": "",
                "format": "cloud",
                "family": provider,
                "families": [provider],
                "parameter_size": str(meta.get("context_window", 0)),
                "quantization_level": "none",
            },
        })

    return tags


def _wallas_model_ids(virtual_models: List[Dict[str, Any]]) -> set:
    ids = {v["id"] for v in virtual_models}
    for m in MODELS_REGISTRY:
        mid = m.get("id")
        if mid:
            ids.add(mid)
    return ids


async def _fetch_ollama_local_tags() -> List[Dict[str, Any]]:
    now = time.monotonic()
    if now - _tag_cache["at"] < _TAG_CACHE_TTL:
        return _tag_cache["models"]
    try:
        async with httpx.AsyncClient(timeout=_UPSTREAM_TIMEOUT) as client:
            r = await client.get(f"{OLLAMA_UPSTREAM}/api/tags")
            if r.status_code == 200:
                data = r.json().get("models", [])
                _tag_cache["models"] = data
                _tag_cache["at"] = now
                return data
    except Exception:
        pass
    _tag_cache["models"] = []
    _tag_cache["at"] = now
    return []


def _map_options(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Translate Ollama 'options' bag into a small set of router kwargs."""
    out: Dict[str, Any] = {}
    if not options:
        return out
    if "temperature" in options:
        out["temperature"] = options["temperature"]
    if "top_p" in options:
        out["top_p"] = options["top_p"]
    if "num_predict" in options:
        out["max_tokens"] = options["num_predict"]
    if "stop" in options:
        out["stop"] = options["stop"]
    return out


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_ollama_router(ai_router, virtual_models: List[Dict[str, Any]]) -> APIRouter:
    """
    Build the APIRouter. We bind `ai_router` (an AIRouter instance) and
    `virtual_models` (the in-memory list from api_server) by closure.
    """
    api = APIRouter(prefix="/api", tags=["ollama"])

    wallas_ids = _wallas_model_ids(virtual_models)

    def _is_wallas(model: str) -> bool:
        # Recompute on every call so newly-fetched cloud models become routable.
        return model in wallas_ids or model in {v["id"] for v in virtual_models} or any(
            m.get("id") == model for m in MODELS_REGISTRY
        )

    # ------------------------------------------------------------------ version
    @api.get("/version")
    async def version():
        return {"version": OLLAMA_VERSION_STRING}

    # ------------------------------------------------------------------ tags
    @api.get("/tags")
    async def tags():
        local = await _fetch_ollama_local_tags()
        cloud = _wallas_models_as_ollama_tags(virtual_models)
        seen: set = set()
        merged: List[Dict[str, Any]] = []
        for entry in list(local) + cloud:
            name = entry.get("name") or entry.get("model")
            if not name or name in seen:
                continue
            seen.add(name)
            merged.append(entry)
        return {"models": merged}

    # ------------------------------------------------------------------ show
    @api.post("/show")
    async def show(body: OllamaShowRequest):
        name = body.name or body.model
        if not name:
            raise HTTPException(status_code=400, detail="missing 'name'")
        if _is_wallas(name):
            meta: Dict[str, Any] = {}
            family = "wallas"
            for v in virtual_models:
                if v["id"] == name:
                    meta = v.get("metadata", {})
                    family = "wallas-virtual"
                    break
            else:
                for m in MODELS_REGISTRY:
                    if m.get("id") == name:
                        meta = m.get("metadata", {})
                        family = m.get("provider", "wallas") or "wallas"
                        break
            ctx = meta.get("context_window", 0)
            return {
                "license": "see WallasAPI",
                "modelfile": f"# Cloud model proxied by WallasAPI\nFROM {name}\n",
                "parameters": f"num_ctx {ctx}",
                "template": "{{ .Prompt }}",
                "details": {
                    "parent_model": "",
                    "format": "cloud",
                    "family": family,
                    "families": [family],
                    "parameter_size": str(ctx),
                    "quantization_level": "none",
                },
                "model_info": {
                    "general.architecture": "cloud",
                    "general.family": family,
                    "general.parameter_count": ctx,
                },
            }
        # Proxy to upstream Ollama
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(f"{OLLAMA_UPSTREAM}/api/show", json={"name": name})
                return JSONResponse(status_code=r.status_code, content=r.json())
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"model '{name}' not found ({e})")

    # ------------------------------------------------------------------ generate
    @api.post("/generate")
    async def generate(body: OllamaGenerateRequest, request: Request):
        if not _is_wallas(body.model):
            return await _proxy_stream(request, "/api/generate")

        system_prompt = body.system or "You are a helpful assistant."
        user_prompt = body.prompt or ""
        stream = bool(body.stream) if body.stream is not None else True
        opts = _map_options(body.options)

        if stream:
            return _wallas_stream_response(
                ai_router, body.model, system_prompt, user_prompt, [], opts,
                shape="generate",
            )
        return _wallas_sync_response(
            ai_router, body.model, system_prompt, user_prompt, [], opts,
            shape="generate",
        )

    # ------------------------------------------------------------------ chat
    @api.post("/chat")
    async def chat(body: OllamaChatRequest, request: Request):
        if not _is_wallas(body.model):
            return await _proxy_stream(request, "/api/chat")

        system_prompt = "You are a helpful assistant."
        history: List[Dict[str, Any]] = []
        user_prompt = ""
        for msg in body.messages:
            if msg.role == "system":
                system_prompt = msg.content or system_prompt
            else:
                history.append({"role": msg.role, "content": msg.content or ""})

        if history and history[-1]["role"] == "user":
            user_prompt = history[-1]["content"]
            history = history[:-1]

        stream = bool(body.stream) if body.stream is not None else True
        opts = _map_options(body.options)

        if stream:
            return _wallas_stream_response(
                ai_router, body.model, system_prompt, user_prompt, history, opts,
                shape="chat",
            )
        return _wallas_sync_response(
            ai_router, body.model, system_prompt, user_prompt, history, opts,
            shape="chat",
        )

    return api


# ---------------------------------------------------------------------------
# Proxy passthrough to upstream Ollama
# ---------------------------------------------------------------------------

async def _proxy_stream(request: Request, path: str) -> StreamingResponse:
    body_bytes = await request.body()
    target = f"{OLLAMA_UPSTREAM}{path}"

    async def iterator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", target, content=body_bytes,
                                         headers={"content-type": "application/json"}) as r:
                    async for chunk in r.aiter_raw():
                        if chunk:
                            yield chunk
        except Exception as e:
            err = json.dumps({"error": f"upstream ollama unreachable: {e}"}) + "\n"
            yield err.encode("utf-8")

    return StreamingResponse(iterator(), media_type="application/x-ndjson")


# ---------------------------------------------------------------------------
# Wallas-routed responses
# ---------------------------------------------------------------------------

def _wallas_sync_response(ai_router, model: str, system_prompt: str,
                          user_prompt: str, history: List[Dict[str, Any]],
                          opts: Dict[str, Any], shape: str) -> JSONResponse:
    reasoning = (model == "razonamiento")
    try:
        text, provider, model_used = ai_router.get_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            preferred_model=model,
            return_metadata=True,
            reasoning=reasoning,
            history=history or None,
        )
    except Exception as e:
        log.error(f"[OLLAMA] sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    created = _iso_now()
    if shape == "generate":
        payload = {
            "model": model_used or model,
            "created_at": created,
            "response": text or "",
            "done": True,
            "done_reason": "stop",
            "context": [],
            "total_duration": 0,
            "load_duration": 0,
            "prompt_eval_count": 0,
            "eval_count": 0,
        }
    else:
        payload = {
            "model": model_used or model,
            "created_at": created,
            "message": {"role": "assistant", "content": text or ""},
            "done": True,
            "done_reason": "stop",
            "total_duration": 0,
            "load_duration": 0,
            "prompt_eval_count": 0,
            "eval_count": 0,
        }
    if provider:
        payload["provider"] = provider
    return JSONResponse(payload)


def _wallas_stream_response(ai_router, model: str, system_prompt: str,
                            user_prompt: str, history: List[Dict[str, Any]],
                            opts: Dict[str, Any], shape: str) -> StreamingResponse:
    reasoning = (model == "razonamiento")

    def line(obj: Dict[str, Any]) -> bytes:
        return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")

    def iterator():
        model_used = model
        eval_count = 0
        t0 = time.time()
        try:
            for chunk in ai_router.stream_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                preferred_model=model,
                reasoning=reasoning,
                history=history or None,
            ):
                ctype = chunk.get("type")
                if ctype == "metadata":
                    model_used = chunk.get("model", model_used) or model_used
                    continue
                if ctype not in ("content", "reasoning"):
                    continue
                delta = chunk.get("chunk", "") or ""
                if not delta:
                    continue
                eval_count += 1
                if shape == "generate":
                    yield line({
                        "model": model_used,
                        "created_at": _iso_now(),
                        "response": delta,
                        "done": False,
                    })
                else:
                    yield line({
                        "model": model_used,
                        "created_at": _iso_now(),
                        "message": {"role": "assistant", "content": delta},
                        "done": False,
                    })
        except Exception as e:
            log.error(f"[OLLAMA] stream error: {e}")
            yield line({"error": str(e), "done": True})
            return

        total_ns = int((time.time() - t0) * 1e9)
        if shape == "generate":
            yield line({
                "model": model_used,
                "created_at": _iso_now(),
                "response": "",
                "done": True,
                "done_reason": "stop",
                "context": [],
                "total_duration": total_ns,
                "load_duration": 0,
                "prompt_eval_count": 0,
                "eval_count": eval_count,
            })
        else:
            yield line({
                "model": model_used,
                "created_at": _iso_now(),
                "message": {"role": "assistant", "content": ""},
                "done": True,
                "done_reason": "stop",
                "total_duration": total_ns,
                "load_duration": 0,
                "prompt_eval_count": 0,
                "eval_count": eval_count,
            })

    return StreamingResponse(iterator(), media_type="application/x-ndjson")
