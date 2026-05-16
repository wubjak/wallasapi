# ai_services/model_fetcher.py
"""
Dynamic model discovery and registration.
Fetches available models from all configured providers at startup and
classifies their capabilities using heuristic rules.
"""
import os
import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

from .config import (
    PROVIDERS, PROVIDER_SPEED_PRIORITY, NON_CHAT_TYPES,
    TEXT, VISION, AUDIO, FILE, FILE_SHIM, REASONING, MOE, FREE,
    CODE, EMBEDDING, RERANK, TTS, IMAGE_GEN, VIDEO_GEN,
    build_model_metadata,
)
from .logger import log

MODELS_CACHE_FILE = os.path.join(os.path.dirname(__file__), "models_cache.json")
MODELS_CACHE_TTL_SECONDS = int(os.getenv("WALLAS_MODELS_CACHE_TTL_SECONDS", "3600"))

# ============================================================================
# Heuristic Capability Classifier
# ============================================================================

_VISION_PATTERNS = [
    "llava", "minicpm", "moondream", "scout",
    "aya-vision", "nemotron-nano-12b-v2-vl", "cosmos", "pixtral",
    "vision", "vl",  # Groq vision models (llama-3.2-vision, etc.)
]
_REASONING_PATTERNS = [
    "-r1", "r1:", "r1-", "o1", "o3", "o4", "reasoning", "thinking", "thought", "qwq",
]
_MOE_PATTERNS = [
    "mixtral", "moe", "jamba", "dbrx", "nemotron", "maverick",
]
_AUDIO_PATTERNS = [
    "whisper", "audio2face", "nemotron-asr", "nemotron-voicechat",
    "active-speaker", "lipsync", "parler", "canary", "parakeet",
    "stt-", "tts-", "audio",
]
_CODE_PATTERNS = [
    "coder", "codestral", "devstral", "starcoder", "code",
]
_EMBEDDING_PATTERNS = [
    "embed", "embedding", "text-embedding",
]
_RERANK_PATTERNS = [
    "rerank",
]
_TTS_PATTERNS = [
    "tts", "lyria",
]
_EXCLUDE_PATTERNS = [
    "robotics", "computer-use", "deep-research", "customtools",
    "prompt-guard", "safeguard", "compound",
    "orpheus",       # Audio synthesis, not chat
    "transcribe",    # Transcription-only, not chat
    "allam",         # Arabic-only experimental
]
_IMAGE_GEN_PATTERNS = [
    "flux", "sdxl", "stable-diffusion", "dall-e", "banana", "seedream",
    "imagen", "z-image-turbo", "midjourney", "recraft", "proteus",
]
_VIDEO_GEN_PATTERNS = [
    "veo", "sora", "ray", "luma", "runway", "gen-2", "gen-3",
    "synthetic-video-detector",
]

# Cohere models that actually work with the OpenAI compatibility API for chat
_COHERE_CHAT_MODELS = [
    "command-a", "command-r", "command-r-plus", "command-r7b",
    "c4ai-aya", "aya-expanse", "aya-vision",
]


def _determine_capabilities(model_id: str, provider: str) -> List[str]:
    """
    Determines model capabilities from its ID string and provider context.
    """
    mid = model_id.lower()

    # --- Exclude non-usable models ---
    if any(pat in mid for pat in _EXCLUDE_PATTERNS):
        return ["excluded"]
        
    if provider == "cerebras" and "gpt-oss" in mid:
        return ["excluded"]

    # --- Embedding (not for chat) ---
    if any(pat in mid for pat in _EMBEDDING_PATTERNS):
        caps = [EMBEDDING]
        _add_free_flag(caps, mid, provider)
        return caps

    # --- Rerank (not for chat) ---
    if any(pat in mid for pat in _RERANK_PATTERNS):
        caps = [RERANK]
        _add_free_flag(caps, mid, provider)
        return caps

    # --- TTS (not for chat) ---
    if any(pat in mid for pat in _TTS_PATTERNS):
        caps = [TTS]
        _add_free_flag(caps, mid, provider)
        return caps

    # --- Audio-only models (Whisper) ---
    if any(pat in mid for pat in _AUDIO_PATTERNS):
        caps = [AUDIO]
        _add_free_flag(caps, mid, provider)
        return caps

    # --- Cohere: Only allow known chat models ---
    if provider == "cohere":
        is_chat = any(pat in mid for pat in _COHERE_CHAT_MODELS)
        if not is_chat:
            # Unknown Cohere model — not usable for chat via compat API
            return ["excluded"]

    # --- NVIDIA / Special Filtering ---
    # Ignore models that are strictly for safety, parsing, or specific tasks not for chat
    tech_keywords = ["-safety", "-guard", "-parse", "-pii", "-deplot", "-gliner", "-ocr", "kosmos-2", "fuyu-8b", "iva-", "imaging-"]
    if any(k in mid.lower() for k in tech_keywords):
        return []

    # --- Standard chat models ---
    caps = [TEXT]

    # Vision
    if any(pat in mid for pat in _VISION_PATTERNS):
        caps.append(VISION)
    elif provider == "gemini":
        caps.append(VISION)

    # Audio (native)
    if provider == "gemini":
        caps.append(AUDIO)

    # Reasoning
    if any(pat in mid for pat in _REASONING_PATTERNS):
        caps.append(REASONING)

    # MoE
    if any(pat in mid for pat in _MOE_PATTERNS):
        caps.append(MOE)

    # Code
    if any(pat in mid for pat in _CODE_PATTERNS):
        caps.append(CODE)

    # TTS
    if any(pat in mid for pat in _TTS_PATTERNS):
        caps.append(TTS)

    # Files
    if provider == "gemini":
        caps.append(FILE)
    else:
        caps.append(FILE_SHIM)

    # Image/Video Gen (non-chat)
    if any(pat in mid for pat in _IMAGE_GEN_PATTERNS):
        caps = [IMAGE_GEN]
    elif any(pat in mid for pat in _VIDEO_GEN_PATTERNS):
        caps = [VIDEO_GEN]
    elif provider == "gemini" and "veo" in mid:
        caps = [VIDEO_GEN]

    # Free
    _add_free_flag(caps, mid, provider)

    return list(set(caps))


def _add_free_flag(caps: list, mid: str, provider: str):
    """Adds the FREE flag based on provider or model name."""
    mid_lower = mid.lower()

    # Providers where ALL chat models are free (rate-limited tiers)
    free_providers = {"groq", "sambanova", "cerebras", "github", "ollama", "huggingface", "pollinations"}
    if provider in free_providers:
        caps.append(FREE)
        return

    # OpenRouter: ONLY :free suffix models are actually free
    if provider == "openrouter":
        if ":free" in mid_lower:
            caps.append(FREE)
        return

    # NVIDIA: Almost all NIMs have a free tier
    if provider == "nvidia":
        caps.append(FREE)
        return

    # Gemini: Flash/Lite are free, Pro also has generous free tier (1500 req/day)
    if provider == "gemini":
        if any(x in mid_lower for x in ["flash", "lite", "gemma", "pro", "nano"]):
            caps.append(FREE)
        return

    # Mistral: Small, Medium, and Pixtral have free tiers. Large/Codestral are paid.
    if provider == "mistral":
        if any(x in mid_lower for x in ["small", "medium", "pixtral"]):
            caps.append(FREE)
        return

    # Cohere: All models have a generous trial/free tier via compat API
    if provider == "cohere":
        caps.append(FREE)
        return


def _extract_metadata(model_id: str) -> Dict[str, Any]:
    """
    Extracts family, parameters (size), and version from model ID.
    Example: 'meta-llama/llama-3.3-70b-instruct' -> {family: 'llama', size: '70b', version: '3.3'}
    """
    mid = model_id.lower()
    meta = {"family": "other", "size": "unknown", "version": "unknown"}

    # Family Detection
    families = ["llama", "qwen", "deepseek", "mistral", "mixtral", "phi", "gemini", "gemma", "claude", "gpt", "command", "nemotron", "cosmos", "jamba"]
    for f in families:
        if f in mid:
            meta["family"] = f
            break
    
    # Size Detection (Regex for 70b, 8b, 175b, etc)
    import re
    # Patterns like 70b, 8b, 7b, 1.5b, 175b, 72b
    size_match = re.search(r'(\d+\.?\d*[btm])', mid)
    if size_match:
        meta["size"] = size_match.group(1)
    
    # Version Detection
    version_match = re.search(r'(\d+\.\d+)', mid)
    if version_match:
        meta["version"] = version_match.group(1)
    elif "llama-4" in mid: meta["version"] = "4.0"
    elif "llama-3.3" in mid: meta["version"] = "3.3"
    elif "llama-3.2" in mid: meta["version"] = "3.2"
    elif "llama-3.1" in mid: meta["version"] = "3.1"
    elif "llama-3" in mid: meta["version"] = "3.0"
    
    return meta


# ============================================================================
# Ollama Cloud Models
# ============================================================================

OLLAMA_CLOUD_MODELS = [
    {"id": "glm-5.1", "name": "GLM 5.1 Cloud"},
    {"id": "gemma4", "name": "Gemma 4 Cloud"},
    {"id": "minimax-m2.7", "name": "MiniMax M2.7 Cloud"},
    {"id": "qwen3.5", "name": "Qwen 3.5 Cloud"},
    {"id": "qwen3-coder-next", "name": "Qwen 3 Coder Cloud"},
    {"id": "qwen3-vl", "name": "Qwen 3 Vision Cloud"},
    {"id": "ministral-3", "name": "Ministral 3 Cloud"},
    {"id": "devstral-small-2", "name": "Devstral Small 2 Cloud"},
    {"id": "nemotron-3-super", "name": "Nemotron 3 Super Cloud"},
    {"id": "qwen3-next", "name": "Qwen 3 Next Cloud"},
    {"id": "kimi-k2.5", "name": "Kimi K2.5 Cloud"},
    {"id": "rnj-1", "name": "Essential AI Rnj-1 Cloud"},
    {"id": "glm-5", "name": "GLM 5 Cloud"},
    {"id": "nemotron-3-nano", "name": "Nemotron 3 Nano Cloud"},
    {"id": "minimax-m2.5", "name": "MiniMax M2.5 Cloud"},
    {"id": "mistral-large-3:675b-cloud", "name": "Mistral Large 3 Cloud"},
]


# ============================================================================
# Async Fetching Logic
# ============================================================================

async def fetch_provider_models(
    session: aiohttp.ClientSession,
    provider_name: str,
    p_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Fetches models from a single provider."""
    base_url = p_config.get("base_url")
    env_key_name = p_config.get("env_key")
    api_key = os.getenv(env_key_name) if env_key_name else None
    models = []

    # --- OpenAI-compatible providers ---
    if provider_name in ("groq", "sambanova", "mistral", "openrouter", "cerebras", "cohere", "nvidia"):
        if not api_key:
            log.debug(f"Saltando {provider_name}: falta {env_key_name}")
            return []
        url = f"{base_url}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as response:
                if response.status == 200:
                    data = await response.json()
                    model_items = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    for m in model_items:
                        m_id = m.get("id")
                        if not m_id:
                            continue
                        caps = _determine_capabilities(m_id, provider_name)
                        if "excluded" in caps:
                            continue
                        models.append({
                            "provider": provider_name,
                            "id": m_id,
                            "capabilities": caps,
                            "meta": _extract_metadata(m_id),
                            "metadata": build_model_metadata(m_id, provider_name, caps),
                            "desc": f"{provider_name.capitalize()}: {m.get('name', m_id)}"
                        })
                    log.info(f"[OK] {provider_name}: {len(models)} modelos")
                else:
                    log.warning(f"[!] {provider_name}: HTTP {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"[T] {provider_name}: timeout")
        except Exception as e:
            log.warning(f"[X] {provider_name}: {e}")

    # --- GitHub Models (special: uses 'name' field as the usable ID) ---
    elif provider_name == "github":
        if not api_key:
            log.debug(f"Saltando github: falta {env_key_name}")
            return []
        url = f"{base_url}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as response:
                if response.status == 200:
                    data = await response.json()
                    model_items = data.get("data", data) if isinstance(data, dict) else data
                    for m in model_items:
                        if isinstance(m, dict):
                            # GitHub returns azureml:// URIs as 'id' but the
                            # usable model name for the API is in the 'name' field.
                            usable_name = m.get("name", "")
                            if not usable_name:
                                continue
                            caps = _determine_capabilities(usable_name, provider_name)
                            if "excluded" in caps:
                                continue
                            models.append({
                                "provider": provider_name,
                                "id": usable_name,
                                "capabilities": caps,
                                "metadata": build_model_metadata(usable_name, provider_name, caps),
                                "desc": f"GitHub: {usable_name}"
                            })
                    log.info(f"[OK] github: {len(models)} modelos")
                else:
                    log.warning(f"[!] github: HTTP {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"[T] github: timeout")
        except Exception as e:
            log.warning(f"[X] github: {e}")

    # --- Ollama (Local + Cloud) ---
    elif provider_name == "ollama":
        url = f"{base_url}/api/tags"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    for m in data.get("models", []):
                        m_id = m.get("name")
                        if m_id:
                            caps = _determine_capabilities(m_id, provider_name)
                            models.append({
                                "provider": provider_name,
                                "id": m_id,
                                "capabilities": caps,
                                "meta": _extract_metadata(m_id),
                                "metadata": build_model_metadata(m_id, provider_name, caps),
                                "desc": f"Local: {m_id}"
                            })
                    log.info(f"[OK] ollama (local): {len(models)} modelos")
        except Exception:
            log.debug("Ollama local no disponible.")

        cloud_count = 0
        for cm in OLLAMA_CLOUD_MODELS:
            caps = _determine_capabilities(cm["id"], provider_name)
            if "excluded" not in caps:
                models.append({
                    "provider": provider_name,
                    "id": cm["id"],
                    "capabilities": caps,
                    "meta": _extract_metadata(cm["id"]),
                    "metadata": build_model_metadata(cm["id"], provider_name, caps),
                    "desc": f"Cloud: {cm['name']}"
                })
                cloud_count += 1
        log.info(f"[OK] ollama (cloud): {cloud_count} modelos")

    # --- Pollinations (Always Free, No Key) ---
    elif provider_name == "pollinations":
        models.append({
            "provider": "pollinations",
            "id": "flux",
            "capabilities": [IMAGE_GEN, FREE],
            "metadata": build_model_metadata("flux", "pollinations", [IMAGE_GEN, FREE]),
            "desc": "Pollinations: Flux (Gratis)"
        })
        models.append({
            "provider": "pollinations",
            "id": "flux-realism",
            "capabilities": [IMAGE_GEN, FREE],
            "metadata": build_model_metadata("flux-realism", "pollinations", [IMAGE_GEN, FREE]),
            "desc": "Pollinations: Flux Realism (Gratis)"
        })
        models.append({
            "provider": "pollinations",
            "id": "any-dark",
            "capabilities": [IMAGE_GEN, FREE],
            "metadata": build_model_metadata("any-dark", "pollinations", [IMAGE_GEN, FREE]),
            "desc": "Pollinations: Anime/Dark (Gratis)"
        })

    # --- Hugging Face (Free Serverless Inference) ---
    elif provider_name == "huggingface":
        # Register popular and free chat/vision/image models
        hf_models = [
            # Chat & Coding
            ("meta-llama/Meta-Llama-3-8B-Instruct", "Llama 3 8B Instruct", [TEXT, FREE]),
            ("mistralai/Mistral-7B-Instruct-v0.3", "Mistral 7B v3", [TEXT, FREE]),
            ("Qwen/Qwen2.5-Coder-32B-Instruct", "Qwen 2.5 Coder 32B", [TEXT, CODE, FREE]),
            ("microsoft/Phi-3.5-mini-instruct", "Phi-3.5 Mini", [TEXT, FREE]),
            # Vision
            ("meta-llama/Llama-3.2-11B-Vision-Instruct", "Llama 3.2 11B Vision", [TEXT, VISION, FREE]),
            # Image Gen
            ("black-forest-labs/FLUX.1-schnell", "Flux.1 Schnell", [IMAGE_GEN, FREE]),
            ("stabilityai/stable-diffusion-xl-base-1.0", "SDXL 1.0", [IMAGE_GEN, FREE]),
            ("runwayml/stable-diffusion-v1-5", "SD v1.5", [IMAGE_GEN, FREE]),
        ]
        for mid, mname, mcaps in hf_models:
            models.append({
                "provider": "huggingface",
                "id": mid,
                "capabilities": mcaps,
                "meta": _extract_metadata(mid),
                "metadata": build_model_metadata(mid, "huggingface", mcaps),
                "desc": f"HuggingFace: {mname}"
            })

    # --- Gemini ---
    elif provider_name == "gemini":
        if not api_key:
            log.debug(f"Saltando Gemini: falta {env_key_name}")
            return []
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=25)) as response:
                if response.status == 200:
                    data = await response.json()
                    for m in data.get("models", []):
                        m_id = m.get("name", "").replace("models/", "")
                        supported_methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in supported_methods:
                            caps = _determine_capabilities(m_id, provider_name)
                            if "excluded" in caps:
                                continue
                            models.append({
                                "provider": provider_name,
                                "id": m_id,
                                "capabilities": caps,
                                "meta": _extract_metadata(m_id),
                                "metadata": build_model_metadata(m_id, provider_name, caps),
                                "desc": f"Gemini: {m.get('displayName', m_id)}"
                            })
                    log.info(f"[OK] gemini: {len(models)} modelos")
                else:
                    log.warning(f"[!] gemini: HTTP {response.status}")
        except asyncio.TimeoutError:
            log.warning(f"[T] gemini: timeout")
        except Exception as e:
            log.warning(f"[X] gemini: {e}")

    return models


async def _fetch_all_models() -> List[Dict[str, Any]]:
    """Fetches models from all providers concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_provider_models(session, name, cfg)
            for name, cfg in PROVIDERS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_models = []
        for res in results:
            if isinstance(res, list):
                all_models.extend(res)
            elif isinstance(res, Exception):
                log.error(f"Error en fetch: {res}")

        return all_models


def _sort_models_by_priority(models: List[Dict]) -> List[Dict]:
    """
    Sorts models so that:
    1. Chat-capable free models from fast providers come first.
    2. Non-chat models (embeddings, rerank, TTS) go to the end.
    """
    priority_map = {p: i for i, p in enumerate(PROVIDER_SPEED_PRIORITY)}

    def sort_key(m):
        caps = set(m.get("capabilities", []))
        provider = m.get("provider", "")

        # Non-chat models go last
        is_non_chat = bool(caps & NON_CHAT_TYPES)
        # Free models come first
        is_free = FREE in caps
        # Provider speed priority
        speed = priority_map.get(provider, 99)

        return (is_non_chat, not is_free, speed, m.get("id", ""))

    return sorted(models, key=sort_key)


# ============================================================================
# Public API
# ============================================================================

async def update_registry_async() -> list:
    """Async version for FastAPI lifespan."""
    from . import config
    try:
        new_models = await _fetch_all_models()
        if new_models:
            sorted_models = _sort_models_by_priority(new_models)
            config.MODELS_REGISTRY.clear()
            config.MODELS_REGISTRY.extend(sorted_models)
            # Count stats
            chat_count = sum(1 for m in sorted_models if TEXT in m.get("capabilities", []))
            free_count = sum(1 for m in sorted_models if FREE in m.get("capabilities", []))
            log.info(f"[R] Registro: {len(sorted_models)} modelos ({chat_count} chat, {free_count} gratis)")
            save_registry_to_cache()
        else:
            log.warning("No se encontraron modelos.")
        return config.MODELS_REGISTRY
    except Exception as e:
        log.error(f"Error en update_registry_async: {e}")
        return config.MODELS_REGISTRY


def load_registry_from_cache() -> bool:
    """Loads models from local JSON cache if it exists."""
    from . import config
    if not os.path.exists(MODELS_CACHE_FILE):
        return False
    try:
        cache_age = max(0, int(time.time() - os.path.getmtime(MODELS_CACHE_FILE)))
        if MODELS_CACHE_TTL_SECONDS > 0 and cache_age > MODELS_CACHE_TTL_SECONDS:
            log.info(f"[CACHE] Caché de modelos expirada ({cache_age}s > {MODELS_CACHE_TTL_SECONDS}s). Refrescando.")
            return False
        with open(MODELS_CACHE_FILE, "r", encoding="utf-8") as f:
            cached_models = json.load(f)
            if cached_models and isinstance(cached_models, list):
                config.MODELS_REGISTRY.clear()
                config.MODELS_REGISTRY.extend(cached_models)
                log.info(f"[CACHE] Cargados {len(cached_models)} modelos desde caché local.")
                return True
    except Exception as e:
        log.warning(f"Error cargando caché de modelos: {e}")
    return False


def save_registry_to_cache():
    """Saves current registry to local JSON file."""
    from . import config
    try:
        with open(MODELS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(config.MODELS_REGISTRY, f, indent=2, ensure_ascii=False)
        log.debug("Caché de modelos actualizada.")
    except Exception as e:
        log.warning(f"Error guardando caché de modelos: {e}")


def update_registry_cache() -> list:
    """Synchronous version for Flask/CLI."""
    from . import config
    try:
        # First try to load from cache
        load_registry_from_cache()

        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop and loop.is_running():
            log.error("update_registry_cache() en contexto async. Usa update_registry_async().")
            return config.MODELS_REGISTRY

        new_models = asyncio.run(_fetch_all_models())
        if new_models:
            sorted_models = _sort_models_by_priority(new_models)
            config.MODELS_REGISTRY.clear()
            config.MODELS_REGISTRY.extend(sorted_models)
            save_registry_to_cache()
            chat_count = sum(1 for m in sorted_models if TEXT in m.get("capabilities", []))
            free_count = sum(1 for m in sorted_models if FREE in m.get("capabilities", []))
            log.info(f"[R] Registro (sync): {len(sorted_models)} modelos ({chat_count} chat, {free_count} gratis)")
        return config.MODELS_REGISTRY
    except Exception as e:
        log.error(f"Error en update_registry_cache: {e}")
        return config.MODELS_REGISTRY
