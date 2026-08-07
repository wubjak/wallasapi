# wallasAPI/router.py
"""
WallasRouter — The orchestration core of WallasAPI.
Routes requests to the best available model across multiple providers,
with automatic fallback, multimodal support, and streaming.
"""
import os
import time
import base64
import subprocess
import glob
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple, Union, Generator

from openai import OpenAI

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from ollama import Client as OllamaClient
from dotenv import load_dotenv

from .config import (
    MODELS_REGISTRY, PROVIDERS, NON_CHAT_TYPES,
    TEXT, VISION, AUDIO, FILE, FILE_SHIM, RAZONAMIENTO, FREE,
    EMBEDDING, RERANK, TTS, MOE, CODE, IMAGE_GEN, VIDEO_GEN,
    RAPIDO, STANDARD, AGENTICO, VISTA, AUTO,
    is_strong_tool_caller,
)
from .memory import MemoryManager
from .file_utils import FileProcessor
from .logger import log
from .model_catalog import RouterResult, VIRTUAL_ALIASES, VIRTUAL_PROFILES, detect_auto_profile, normalize_model, rank_candidates

# Media storage
TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_MEDIA_DIR = os.path.join(TEMPLATE_DIR, "temp_media")
os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)

# MIME types that should be treated as audio, not files
AUDIO_MIME_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg",
    "audio/webm", "audio/flac", "audio/aac", "audio/m4a",
    "audio/x-m4a", "audio/mp4",
}

# ============================================================================
# Model Aliases
# ============================================================================

MODEL_ALIASES = {
    "gpt-4o": ["gemini-2.0-flash", "gpt-4o", "llama-3.3-70b-versatile"],
    "gpt-4": ["gpt-4o", "gemini-2.5-pro", "llama-3.3-70b-versatile"],
    "gpt-3.5-turbo": ["gemini-2.0-flash-lite", "llama-3.1-8b-instant"],
    "claude-3-5-sonnet": ["gemini-2.5-pro", "llama-3.3-70b-versatile"],
    "claude-3-opus": ["gemini-2.5-pro"],
    "claude-3-haiku": ["gemini-2.0-flash-lite"],
    "deepseek-chat": ["DeepSeek-V3.2", "llama-3.3-70b-versatile"],
    "deepseek-reasoner": ["DeepSeek-R1-0528", "gemini-2.5-flash"],
    # Expanded aliases for IDE compatibility
    "claude-3-5-sonnet-20240620": ["claude-3-5-sonnet"],
    "claude-3-5-sonnet-20241022": ["claude-3-5-sonnet"],
    "gpt-4o-2024-05-13": ["gpt-4o"],
    "gpt-4o-2024-08-06": ["gpt-4o"],
    "gpt-4o-mini-2024-07-18": ["gpt-4o-mini"],
}


class AIRouter:
    """
    Intelligent multi-provider AI router with fallback, streaming,
    multimodal support, and automatic audio detection.
    """

    MAX_CANDIDATES = 25
    STICKY_TTL_SECONDS = 300
    # Per-provider request timeout. NVIDIA NIM serverless and OpenRouter cold-starts
    # can easily exceed 10 s, and agent workloads (Hermes/Cursor/etc.) ship large
    # tool schemas that take longer to process. 60 s is a sane default; lower it
    # via WALLAS_REQUEST_TIMEOUT_SECONDS=8 for hot/local setups.
    REQUEST_TIMEOUT_SECONDS = float(os.getenv("WALLAS_REQUEST_TIMEOUT_SECONDS", "60.0"))

    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self._circuit: Dict[str, Dict[str, Any]] = {}  # "provider/model" -> {failed_at, fail_count, success_count, avg_latency_ms, last_error}
        self._last_success_cache: Dict[str, Tuple[str, str, float]] = {}  # thread_id -> (provider, model, timestamp)

    # --- Circuit Breaker helpers ---

    def _circuit_key(self, provider_name: str, model_id: str) -> str:
        return f"{provider_name}/{model_id}"

    def _is_available(self, key: str) -> bool:
        state = self._circuit.get(key)
        if not state:
            return True
        failed_at = state.get("failed_at", 0)
        if failed_at == 0:
            return True
        fail_count = state.get("fail_count", 0)
        # Exponential backoff: 300s, 600s, 1800s
        cooldowns = [0, 300, 600, 1800]
        idx = min(fail_count, len(cooldowns) - 1)
        cooldown = cooldowns[idx]
        return time.time() >= failed_at + cooldown

    def _mark_failure(self, key: str, reason: str) -> None:
        state = self._circuit.setdefault(key, {"fail_count": 0, "success_count": 0, "avg_latency_ms": 0.0})
        state["failed_at"] = time.time()
        state["fail_count"] = state.get("fail_count", 0) + 1
        state["last_error"] = reason
        log.info(f"[CIRCUIT] {key} falló ({reason}). Cooldown activado. Fallos consecutivos: {state['fail_count']}")

        if reason == "not_found":
            provider, model_id = key.split("/", 1)
            before = len(MODELS_REGISTRY)
            MODELS_REGISTRY[:] = [
                m for m in MODELS_REGISTRY
                if not (m.get("provider") == provider and m.get("id") == model_id)
            ]
            if len(MODELS_REGISTRY) != before:
                log.warning(f"[REGISTRY] Modelo removido del runtime por not_found: {key}")
                try:
                    from .model_fetcher import save_registry_to_cache
                    save_registry_to_cache()
                except Exception as e:
                    log.warning(f"[REGISTRY] No se pudo persistir remoción de {key}: {e}")

    def _mark_success(self, key: str, latency_ms: float, thread_id: str = None) -> None:
        state = self._circuit.setdefault(key, {"fail_count": 0, "success_count": 0, "avg_latency_ms": 0.0})
        state["success_count"] = state.get("success_count", 0) + 1
        state["fail_count"] = 0
        state["failed_at"] = 0
        alpha = 0.3
        prev = state.get("avg_latency_ms", 0.0)
        state["avg_latency_ms"] = alpha * latency_ms + (1 - alpha) * prev if prev > 0 else latency_ms
        if thread_id:
            provider, model = key.split("/", 1)
            self._last_success_cache[thread_id] = (provider, model, time.time())

    def get_circuit_stats(self) -> Dict[str, Any]:
        return {
            "circuits": [
                {
                    "key": k,
                    "fail_count": v.get("fail_count", 0),
                    "success_count": v.get("success_count", 0),
                    "avg_latency_ms": round(v.get("avg_latency_ms", 0.0), 1),
                    "failed_at": v.get("failed_at", 0),
                    "cooldown_seconds_remaining": max(0, (v.get("failed_at", 0) + [0, 300, 600, 1800][min(v.get("fail_count", 0), 3)]) - time.time()) if v.get("failed_at", 0) else 0,
                    "last_error": v.get("last_error", ""),
                }
                for k, v in self._circuit.items()
            ],
            "timestamp": time.time(),
        }

    def _sort_candidates(self, candidates: List[Dict[str, Any]], thread_id: str = None) -> List[Dict[str, Any]]:
        """
        Smart sort: sticky routing (last success for this thread) + EMA latency.
        Returns candidates with fastest/known-good models first.
        """
        if not candidates:
            return candidates

        sticky = None
        if thread_id and thread_id in self._last_success_cache:
            provider, model, ts = self._last_success_cache[thread_id]
            if time.time() - ts < self.STICKY_TTL_SECONDS:
                for i, c in enumerate(candidates):
                    if c.get("provider") == provider and c.get("id") == model and self._is_available(f"{provider}/{model}"):
                        sticky = candidates.pop(i)
                        break

        def _latency_key(m):
            key = f"{m['provider']}/{m['id']}"
            state = self._circuit.get(key)
            if state:
                # Lower EMA latency = higher priority (sort ascending)
                # Models with 0 latency (unknown) get a moderate penalty so tried models rank better
                ema = state.get("avg_latency_ms", 0.0)
                if ema > 0:
                    return ema
            # Unknown latency: deprioritize slightly behind known fast models
            return 99999.0

        candidates.sort(key=_latency_key)

        if sticky:
            log.info(f"[ROUTER] Sticky routing: reintentando último éxito {sticky['provider']}/{sticky['id']} para thread {thread_id}")
            candidates.insert(0, sticky)

        return candidates

    def get_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """
        Generates embeddings for a list of texts using available providers.
        Prioritizes OpenAI/NVIDIA/Ollama.
        """
        # Try different providers for embeddings
        embedding_providers = ["nvidia", "openai", "github", "ollama"]
        
        for provider in embedding_providers:
            p_cfg = PROVIDERS.get(provider)
            if not p_cfg: continue
            
            api_key = os.getenv(p_cfg.get("env_key", ""))
            if provider != "ollama" and not api_key: continue
            
            try:
                if provider in ("openai", "nvidia", "github"):
                    client = OpenAI(base_url=p_cfg["base_url"], api_key=api_key)
                    res = client.embeddings.create(input=texts, model=model)
                    return [item.embedding for item in res.data]
                
                elif provider == "ollama":
                    client = OllamaClient(host=p_cfg["base_url"])
                    # Default ollama model if none specified
                    m = model if ":" in model else "nomic-embed-text"
                    results = []
                    for t in texts:
                        res = client.embeddings(model=m, prompt=t)
                        results.append(res["embedding"])
                    return results
            except Exception as e:
                log.warning(f"[ROUTER-EMBED] {provider} failed: {e}")
                continue
        
        # Final fallback: zero vectors
        log.error("[ROUTER-EMBED] All providers failed. Returning zero vectors.")
        return [[0.0] * 1536 for _ in texts]

    # ========================================================================
    # Input Pre-Processing
    # ========================================================================

    @staticmethod
    def _separate_audio_from_files(
        files: List[Dict[str, str]] = None,
        audio: List[Dict[str, str]] = None,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Scans the 'files' list for audio MIME types and moves them to the
        'audio' list automatically. This ensures that an MP3 uploaded via
        the file button gets routed to an audio-capable model like Gemini.
        
        Returns: (cleaned_files, merged_audio)
        """
        if not files:
            return (files or []), (audio or [])

        clean_files = []
        merged_audio = list(audio or [])

        for f in files:
            mime = f.get("mime_type", "").lower()
            if mime in AUDIO_MIME_TYPES:
                log.info(f"[AUDIO-DETECT] Archivo '{f.get('name', '?')}' ({mime}) reclasificado como audio.")
                merged_audio.append(f)
            else:
                clean_files.append(f)

        return clean_files, merged_audio

    def _load_dynamic_aliases(self):
        """Carga los mapeos de modelos desde models.env para que coincidan con la configuración del Dashboard."""
        try:
            # Intentar encontrar models.env en la carpeta de openclaude
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(project_root, "openclaude", "models.env")
            
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.startswith("#"):
                            key, val = line.strip().split("=", 1)
                            # Actualizar alias globales
                            if key == "ANTHROPIC_DEFAULT_OPUS_MODEL":
                                MODEL_ALIASES["claude-3-opus"] = [val]
                            elif key == "ANTHROPIC_DEFAULT_SONNET_MODEL":
                                MODEL_ALIASES["claude-3-5-sonnet"] = [val]
                                MODEL_ALIASES["claude-3-sonnet"] = [val]
                            elif key == "ANTHROPIC_DEFAULT_HAIKU_MODEL":
                                MODEL_ALIASES["claude-3-haiku"] = [val]
                            elif key == "OPENAI_MODEL":
                                MODEL_ALIASES["gpt-4o"] = [val]
                                MODEL_ALIASES["gpt-4"] = [val]
        except Exception as e:
            log.warning(f"[CONFIG] No se pudieron cargar los alias dinámicos: {e}")

    # ========================================================================
    # Model Selection
    # ========================================================================

    def _get_ordered_model_list(
        self,
        preferred_provider: str = None,
        preferred_model: str = None,
        prioritize_reasoning: bool = False,
        prompt_len: int = 0,
        user_prompt: str = "",
        images: bool = False,
        files: bool = False,
        audio: bool = False,
        tools: bool = False,
        cost_mode: str = "free_only",
    ) -> List[Dict]:
        """
        Returns MODELS_REGISTRY sorted with preferred model/provider first.
        Excludes non-chat models (embeddings, rerank, TTS) from the list.
        """
        # Cargar mapeos frescos del Dashboard
        self._load_dynamic_aliases()
        
        # Filter out non-chat models for completion requests (unless explicitly requested via category)
        is_category_request = preferred_model in [RAPIDO, STANDARD, RAZONAMIENTO, AGENTICO, VISTA, AUTO]
        
        chat_models = [
            m for m in MODELS_REGISTRY
            if (TEXT in m.get("capabilities", []) or is_category_request) and not (set(m.get("capabilities", [])) & NON_CHAT_TYPES - ({preferred_model} if is_category_request else set()))
        ]

        # Cost policy is enforced before *every* ordering path, including a
        # concrete model id.  An unknown/trial/paid route cannot become a
        # surprise bill merely because the caller bypassed a virtual profile.
        if cost_mode != "allow_paid" or os.getenv("WALLAS_ALLOW_PAID", "false").lower() != "true":
            chat_models = [
                model for model in chat_models
                if normalize_model(model.get("provider", ""), model.get("id", ""), model.get("source_metadata")).cost_class
                in {"local", "free_endpoint", "free_tier"}
            ]
        self._last_routing_plan = {
            "requested_profile": preferred_model or "standard", "profile": "exact_model" if preferred_model else "standard",
            "signals": ["explicit_model"] if preferred_model else ["default"], "confidence": 1.0,
            "candidates": [], "rejected": [],
        }

        # V2 virtual profiles are strict capability filters, never provider-wide
        # guesses.  Keep a compact plan for the explain endpoint and for logs.
        raw_requested = (preferred_model or "").lower()
        requested = VIRTUAL_ALIASES.get(raw_requested, raw_requested)
        if requested in VIRTUAL_PROFILES or requested == AUTO:
            router_mode = os.getenv("WALLAS_ROUTER_MODE", "v2").lower()
            if router_mode not in {"legacy", "shadow", "v2"}:
                router_mode = "v2"
            legacy_supported = raw_requested in {RAPIDO, STANDARD, RAZONAMIENTO, AGENTICO, VISTA, AUTO}

            # Legacy can only handle the historical virtual ids. New profiles
            # always use V2, even while an operator is rolling old tiers back.
            if router_mode != "legacy" or not legacy_supported:
                profile, signals, confidence = (requested, [], 1.0)
                if requested == AUTO:
                    profile, signals, confidence = detect_auto_profile(
                        user_prompt, images=images, audio=audio, files=files,
                        tools=tools, reasoning=prioritize_reasoning,
                        required_context=max(0, int(prompt_len / 3) + 4096),
                    )
                required_modalities = {TEXT}
                if images: required_modalities.add("image")
                if audio: required_modalities.add("audio")
                if files: required_modalities.add("file")
                candidates, rejected = rank_candidates(
                    chat_models, profile=profile,
                    required_context=max(0, int(prompt_len / 3) + 4096),
                    required_modalities=required_modalities, tools_requested=tools,
                    cost_mode=cost_mode,
                    allow_paid=os.getenv("WALLAS_ALLOW_PAID", "false").lower() == "true" and cost_mode == "allow_paid",
                    preferred_provider=preferred_provider,
                )
                self._last_routing_plan = {
                    "requested_profile": requested, "profile": profile,
                    "signals": signals, "confidence": confidence, "router_mode": router_mode,
                    "candidates": [{"provider": m.get("provider"), "id": m.get("id")} for m in candidates],
                    "rejected": rejected,
                }
                if router_mode == "v2" or not legacy_supported:
                    return candidates
                # Shadow records V2 and falls through to legacy ordering.
                self._last_routing_plan["shadow_candidates"] = list(self._last_routing_plan["candidates"])

        # Context-Aware Filtering: If prompt is large, deprioritize models with known small contexts
        is_large = prompt_len > 15000 # ~4k-5k tokens
        if is_large:
            log.info(f"[ROUTER] Detectado prompt grande ({prompt_len} caracteres). Aplicando penalización de contexto.")
        
        # Logic-rich Sorting for Auto-routing
        def sort_key(m):
            caps = m.get("capabilities", [])
            provider = m.get("provider", "")
            mid = m.get("id", "").lower()
            m_meta = m.get("meta", {})
            
            priority = 99
            try:
                f_flag = globals().get("FREE", "free")
                r_flag = globals().get("REASONING", "reasoning")
                
                is_free = f_flag in caps
                has_reasoning = r_flag in caps
                is_moe = MOE in caps
                
                # Context-aware penalty: use the model's actual context_window
                # from metadata instead of the old hardcoded provider list
                # (which was overly punitive — Groq Llama 3.3 70B, SambaNova
                # 405B, etc. all have 128K contexts now). Reserve ~4K tokens
                # (~16K chars) of headroom for the response.
                ctx_window = (m_meta or {}).get("context_window", 0) or 0
                if ctx_window > 0:
                    ctx_chars = ctx_window * 4  # ~4 chars per token
                    needed_chars = prompt_len + 16000  # response headroom
                    has_context_risk = ctx_chars < needed_chars
                else:
                    # Fallback for models with no context_window metadata:
                    # only penalize obviously-tiny models by name.
                    is_small_model = any(s in mid for s in ["8b", "7b", "3b", "1b", "0.5b", "nano"])
                    has_context_risk = is_large and is_small_model

                # If a specific category was requested as 'preferred_model'
                if is_category_request:
                    # REGLA DE ORO: Si es una categoría automática, lo GRATIS va primero siempre.
                    if is_free:
                        priority = 0 # Prioridad absoluta para lo que ya cargó como gratis
                    else:
                        priority = 50 # Los de pago van al final del todo
                    
                    # Refinamiento por categoría
                    if preferred_model == RAPIDO:
                        # Prioritize fastest providers
                        if provider in ["cerebras", "groq"]: priority -= 5
                        elif provider in ["nvidia", "sambanova"]: priority -= 2
                    elif preferred_model == RAZONAMIENTO or (preferred_model == AUTO and prioritize_reasoning):
                        # Prioritize reasoning capability (REASONING is the tag, RAZONAMIENTO is the category)
                        if globals().get("REASONING", "reasoning") in caps or "r1" in mid: priority -= 5
                    elif preferred_model == STANDARD:
                        # Prioritize high-quality balanced models
                        if "sonnet" in mid or "gpt-4o" in mid: priority -= 5
                        elif "gemini-2.0-flash" in mid: priority -= 3
                    elif preferred_model == AGENTICO:
                        # Reliable multi-step tool callers only. Strong penalty
                        # for models outside the curated list so the tier stays
                        # trustworthy for agentic loops.
                        # STRICT-FREE: paid models are pushed so far down they
                        # are effectively unreachable. Users opt into agentico
                        # specifically because their free tier is enough — a
                        # silent fallback to a paid model would surprise them
                        # with billing. If all free strong callers fail, the
                        # request errors out, which is the desired behavior.
                        if not is_free:
                            priority += 1000
                        if is_strong_tool_caller(mid):
                            priority -= 8
                        else:
                            priority += 100  # effectively excluded
                    elif preferred_model == VISTA:
                        # Vision-capable models. Free preference is already
                        # baked in via the is_free check above (prio 0 vs 50).
                        # Hard-filter non-vision so the tier stays meaningful.
                        if VISION in caps:
                            priority -= 8
                            # Prefer larger context inside the tier
                            if not is_small_model:
                                priority -= 2
                        else:
                            priority += 100  # effectively excluded
                    elif preferred_model == AUTO:
                        # Balanced logic: High context + Quality
                        if is_large: priority -= 5
                        if "sonnet" in mid: priority -= 2
                elif prioritize_reasoning:
                    if (globals().get("REASONING", "reasoning") in caps or "r1" in mid) and is_free: priority = 0
                    elif (globals().get("REASONING", "reasoning") in caps or "r1" in mid): priority = 1
                    elif is_free: priority = 2
                    else: priority = 3
                else:
                    # STANDARD TEXT REQUEST: Prioritize MoE for efficiency
                    if not has_reasoning and is_free: 
                        priority = 0.5 if is_moe else 1
                    elif not has_reasoning: 
                        priority = 1.5 if is_moe else 2
                    elif is_free: priority = 3
                    else: priority = 4
                
                if has_context_risk:
                    priority += 10 # Send to the end of its tier
            except Exception as e:
                log.warning(f"[ROUTER] sort_key error for {m.get('id', '?')}: {e}")
                priority = 99
            
            # Stable tie-breaker: same input and health state yields same order.
            return (priority, f"{provider}::{m.get('id', '')}")

        if not preferred_model and not preferred_provider:
            chat_models.sort(key=sort_key)
            return chat_models

        # Virtual-tier routing — when preferred_model is a tier name (rapido,
        # standard, razonamiento, agentico, vista, auto), there is no concrete
        # catalog id to match. Skip the per-id lookup chain below and rank
        # via sort_key, which already has the tier-aware priority math.
        # Without this branch the function falls all the way through line 562
        # and returns chat_models in cache-load order — silently defeating
        # every tier including the legacy ones.
        if preferred_model in [RAPIDO, STANDARD, RAZONAMIENTO, AGENTICO, VISTA, AUTO]:
            chat_models.sort(key=sort_key)
            legacy_candidates = [{"provider": m.get("provider"), "id": m.get("id")} for m in chat_models]
            if self._last_routing_plan.get("router_mode") == "shadow":
                self._last_routing_plan["legacy_candidates"] = legacy_candidates
            else:
                self._last_routing_plan = {
                    "requested_profile": preferred_model, "profile": preferred_model,
                    "signals": ["legacy_router"], "confidence": 1.0,
                    "router_mode": "legacy", "candidates": legacy_candidates, "rejected": [],
                }
            return chat_models

        if preferred_model:
            # ---- Provider:model disambiguation parser ----
            # Canonical new form: "provider:model_id" (uses colon, never collides
            # with publisher prefixes like 'meta/' or 'mistralai/' inside the id).
            # Legacy form: "provider/model_id" — only split on '/' when the first
            # segment is a *real* provider in PROVIDERS. Otherwise the slash is
            # part of the publisher prefix and the id stays intact.
            if preferred_model not in [RAPIDO, STANDARD, RAZONAMIENTO, AGENTICO, VISTA, AUTO]:
                if ":" in preferred_model:
                    cand_prov, _, rest = preferred_model.partition(":")
                    if cand_prov.lower() in PROVIDERS:
                        if not preferred_provider:
                            preferred_provider = cand_prov.lower()
                        preferred_model = rest
                elif "/" in preferred_model:
                    first_seg = preferred_model.split("/", 1)[0].lower()
                    if first_seg in PROVIDERS:
                        if not preferred_provider:
                            preferred_provider = first_seg
                        preferred_model = preferred_model.split("/", 1)[1]
                    # else: first segment is a publisher prefix (meta/, mistralai/,
                    # google/, nvidia/, qwen/, etc.). Leave preferred_model intact
                    # so the catalog match works against ids like "meta/llama-3.3".
            # 1. Alias resolution (First check if it's a known alias like 'gpt-4o')
            alias_ids = MODEL_ALIASES.get(preferred_model.lower(), [])
            actual_pref = alias_ids[0] if alias_ids else preferred_model
            pref_low = actual_pref.lower()

            # 2. Extract metadata for the target model
            from .model_fetcher import _extract_metadata
            pref_meta = _extract_metadata(actual_pref)
            
            ordered_matches = []
            penalized_matches = []
            
            # --- Tier 1 & 2: Exact ID + Provider Redundancy ---
            exact_matches = [m for m in chat_models if m["id"].lower() == pref_low]
            known_but_ineligible = any(m.get("id", "").lower() == pref_low for m in MODELS_REGISTRY) and not exact_matches
            if known_but_ineligible:
                self._last_routing_plan = {
                    "requested_profile": preferred_model, "profile": "exact_model",
                    "signals": ["exact_model"], "confidence": 1.0, "candidates": [],
                    "rejected": [{"id": actual_pref, "reason": "cost_or_lifecycle_ineligible"}],
                }
                return []
            
            # Filter exact matches for context risk
            safe_exact = []
            for m in exact_matches:
                provider = m.get("provider", "").lower()
                mid = m.get("id", "").lower()
                if is_large and (provider in ["sambanova", "groq", "cerebras"] or any(s in mid for s in ["8b", "7b", "3b", "nano"])):
                    penalized_matches.append(m)
                else:
                    safe_exact.append(m)

            if preferred_provider:
                p_matches = [m for m in safe_exact if m["provider"] == preferred_provider]
                other_provs = [m for m in safe_exact if m not in p_matches]
                ordered_matches.extend(p_matches)
                ordered_matches.extend(other_provs)
            else:
                from .config import PROVIDER_SPEED_PRIORITY
                p_map = {p: i for i, p in enumerate(PROVIDER_SPEED_PRIORITY)}
                
                # High-Context Priority: Gemini and NVIDIA are best for large prompts
                def safe_sort_key(m):
                    provider = m.get("provider", "").lower()
                    mid = m.get("id", "").lower()
                    if is_large:
                        # SUPER PRIORITY: Gemini Pro for very long histories (>40k chars)
                        if prompt_len > 40000:
                            if provider == "gemini" and "pro" in mid: return 0
                            if provider == "gemini": return 1
                        else:
                            if provider == "gemini" and "2.0-flash" in mid: return 0
                            if provider == "gemini": return 1
                        
                        if provider == "nvidia": return 2
                        if provider == "github": return 3
                        return 4
                    return p_map.get(provider, 99)

                safe_exact.sort(key=safe_sort_key)
                ordered_matches.extend(safe_exact)

            # --- Tier 3: Siblings (Same Family, Size and Version) ---
            if pref_meta["family"] != "other":
                siblings = [
                    m for m in chat_models 
                    if m not in ordered_matches and
                    m.get("meta", {}).get("family") == pref_meta["family"] and
                    m.get("meta", {}).get("size") == pref_meta["size"] and
                    m.get("meta", {}).get("version") == pref_meta["version"]
                ]
                ordered_matches.extend(siblings)

                # --- Tier 4: Family Cousins (Same Family, any size/version) ---
                cousins = [
                    m for m in chat_models 
                    if m not in ordered_matches and
                    m.get("meta", {}).get("family") == pref_meta["family"]
                ]
                ordered_matches.extend(cousins)

            # --- Tier 5: Class Mates (Same Size, different family) ---
            if pref_meta["size"] != "unknown":
                classmates = [
                    m for m in chat_models 
                    if m not in ordered_matches and
                    m.get("meta", {}).get("size") == pref_meta["size"]
                ]
                ordered_matches.extend(classmates)

            # --- Tier 6: Fuzzy fallback (last resort match) ---
            if not ordered_matches:
                fuzzy = [m for m in chat_models if pref_low in m["id"].lower() or m["id"].lower() in pref_low]
                ordered_matches.extend(fuzzy)

            if ordered_matches or penalized_matches:
                remaining = [m for m in chat_models if m not in ordered_matches and m not in penalized_matches]
                # Split remaining into safe and risky
                safe_rem = []
                risky_rem = []
                for m in remaining:
                    provider = m.get("provider", "").lower()
                    mid = m.get("id", "").lower()
                    if is_large and (provider in ["sambanova", "groq", "cerebras"] or any(s in mid for s in ["8b", "7b", "3b", "nano"])):
                        risky_rem.append(m)
                    else:
                        safe_rem.append(m)
                
                # Final Order: Safe matches -> Safe remaining -> All risky/penalized
                # Sort safe_rem by high-context priority too
                def rem_sort_key(m):
                    provider = m.get("provider", "").lower()
                    mid = m.get("id", "").lower()
                    if is_large:
                        if provider == "gemini" and "2.0-flash" in mid: return 0
                        if provider == "gemini": return 1
                        if provider == "nvidia": return 2
                        if provider == "github": return 3
                    return 4
                
                safe_rem.sort(key=rem_sort_key)
                return ordered_matches + safe_rem + risky_rem + penalized_matches

        elif preferred_provider:
            main = [m for m in chat_models if m["provider"] == preferred_provider]
            rest = [m for m in chat_models if m["provider"] != preferred_provider]
            return main + rest

        return chat_models

    def generate_chat_title(self, user_prompt: str) -> str:
        """Generates a short, descriptive title for the chat based on the first prompt."""
        try:
            prompt = f"Genera un título muy corto (máximo 5 palabras) para una conversación que empieza así: '{user_prompt}'. Responde SOLO con el título, sin comillas ni puntos finales."
            # We use the router to get a completion using any available fast model
            title = self.get_completion(
                system_prompt="Eres un experto en resumir conversaciones.",
                user_prompt=prompt
            )
            if title.startswith(("ERROR", "[ERROR", "[Error")) or len(title) > 100:
                return "Nueva Conversación"
            return title.strip().replace("\"", "").replace("'", "")
        except Exception as e:
            log.warning(f"Error generando título: {e}")
            return "Nueva Conversación"

    def interpret_image(self, image_b64: str, preferred_model: str = None) -> str:
        """Analyzes an image and returns a textual description using a vision model."""
        try:
            # We use a broad prompt that any model, local or cloud, can try to answer
            prompt = "Describe detalladamente qué hay en esta imagen."
            
            # Use the preferred model if specified, falling back to gemini or any other vision model
            description = self.get_completion(
                system_prompt="Eres un experto en análisis visual muy detallado.",
                user_prompt=prompt,
                images=[image_b64.split(",")[-1]],
                preferred_model=preferred_model or "gemini-2.0-flash"
            )
            return description
        except Exception as e:
            log.error(f"Error interpretando imagen: {e}")
            return "[Error interpretando imagen]"

    def _split_audio(self, audio_path: str, segment_time_seconds: int = 600) -> List[str]:
        """Splits audio into smaller chunks using ffmpeg to stay under API limits (25MB)."""
        if not os.path.exists(audio_path):
            return []
        
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        if file_size_mb < 20: # No need to split
            return [audio_path]

        log.info(f"[AUDIO] Fragmentando {os.path.basename(audio_path)} ({file_size_mb:.1f}MB) en partes de {segment_time_seconds}s...")
        
        base_dir = os.path.dirname(audio_path)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        chunk_pattern = os.path.join(base_dir, f"chunk_{base_name}_%03d.mp3")
        
        # Clean old chunks
        for f in glob.glob(os.path.join(base_dir, f"chunk_{base_name}_*.mp3")):
            try: os.remove(f)
            except: pass
            
        # Try local ffmpeg if exists
        ffmpeg_cmd = "ffmpeg"
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        local_ffmpeg = os.path.join(project_root, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            ffmpeg_cmd = local_ffmpeg
            
        cmd = [
            ffmpeg_cmd, "-y", "-i", audio_path, 
            "-f", "segment", "-segment_time", str(segment_time_seconds), 
            "-c", "copy", chunk_pattern
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            chunks = sorted(glob.glob(os.path.join(base_dir, f"chunk_{base_name}_*.mp3")))
            return chunks if chunks else [audio_path]
        except Exception as e:
            log.error(f"[AUDIO] Error dividiendo audio: {e}")
            return [audio_path]

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribes audio using remote providers.
        Implements chunking and multi-provider fallback.
        """
        chunks = self._split_audio(audio_path)
        if not chunks:
            return None
            
        final_transcription = []
        
        # Get all audio-capable models from registry
        audio_models = [m for m in MODELS_REGISTRY if AUDIO in m.get("capabilities", [])]
        
        # Sort by provider speed priority
        from .config import PROVIDER_SPEED_PRIORITY
        priority_map = {p: i for i, p in enumerate(PROVIDER_SPEED_PRIORITY)}
        audio_models.sort(key=lambda m: priority_map.get(m["provider"], 99))

        for i, chunk in enumerate(chunks):
            log.info(f"[TRANSCRIPTION] Procesando fragmento {i+1}/{len(chunks)}...")
            chunk_text = None
            
            # Try each model until one succeeds
            for model_info in audio_models:
                provider = model_info["provider"]
                model_id = model_info["id"]
                api_key = os.getenv(PROVIDERS[provider].get("env_key", ""))
                
                if not api_key: continue
                
                try:
                    if provider in ("groq", "nvidia", "sambanova", "mistral", "openai", "cerebras"):
                        # OpenAI-compatible audio API
                        base_url = PROVIDERS[provider]["base_url"]
                        client = OpenAI(base_url=base_url, api_key=api_key)
                        with open(chunk, "rb") as f:
                            res = client.audio.transcriptions.create(
                                model=model_id,
                                file=f,
                                response_format="text"
                            )
                            chunk_text = res.strip()
                    
                    elif provider == "gemini":
                        # Multimodal prompt fallback
                        with open(chunk, "rb") as f:
                            audio_data = base64.b64encode(f.read()).decode()
                        
                        res = self.get_completion(
                            system_prompt="Eres un experto transcriptor. Transcribe el audio adjunto palabra por palabra. Responde SOLO con el texto transcrito.",
                            user_prompt="Transcribe este audio.",
                            audio=[{"data": audio_data, "mime_type": "audio/mp3"}],
                            preferred_model=model_id
                        )
                        if res and "ERROR" not in res:
                            chunk_text = res.strip()

                    if chunk_text:
                        log.info(f"[OK] Fragmento {i+1} transcrito con {provider}/{model_id}")
                        break 
                    
                except Exception as e:
                    log.warning(f"[!] {provider}/{model_id} falló en fragmento {i+1}: {e}")
                    continue 
            
            if chunk_text:
                final_transcription.append(chunk_text)
            else:
                log.error(f"[FAIL] No se pudo transcribir el fragmento {i+1} con ningún proveedor.")
                # We return what we have so far if some chunks succeeded, 
                # or None if first chunk failed to trigger local fallback.
                if i == 0: return None
                break
        
        return " ".join(final_transcription).strip() if final_transcription else None

    # ========================================================================
    # Context Enrichment
    # ========================================================================

    def _prepare_context(
        self,
        system_prompt: str,
        provider_name: str,
        files: List[Dict[str, str]] = None,
        user_prompt: str = "",
        reasoning: bool = False,
    ) -> Tuple[str, str]:
        """Enriches system prompt. Returns (enriched_prompt, shim_notice)."""
        shim_notice = ""
        
        if not reasoning:
            system_prompt += "\n\n[INSTRUCCIÓN ESTRICTA DEL SISTEMA]: Debes responder de forma directa y asertiva al usuario. NO pienses paso a paso. NO utilices razonamiento interno ni generes texto dentro de etiquetas <think> o similares. Omite cualquier preludio y ve directo a la respuesta."

        if files and provider_name != "gemini":
            file_context, shim_notice = FileProcessor.format_as_context(files, notify_shim=True)
            if file_context:
                system_prompt += f"\n\n{file_context}"

        return system_prompt, shim_notice

    # ========================================================================
    # Streaming Completion
    # ========================================================================
    def stream_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[str] = None,
        files: List[Dict[str, str]] = None,
        audio: List[Dict[str, str]] = None,
        thread_id: str = None,
        preferred_provider: str = None,
        preferred_model: str = None,
        reasoning: bool = False,
        retain_file_context: bool = False,
        tools: List[Dict[str, Any]] = None,
        tool_choice: Union[str, Dict[str, Any]] = None,
        history: List[Dict[str, Any]] = None,
        cost_mode: str = "free_only",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generator yielding chunks: {type, chunk, provider?, model?}
        type: 'content', 'reasoning', 'metadata', 'shim_notice'
        """
        # Auto-detect audio files
        files, audio = self._separate_audio_from_files(files, audio)

        has_images = bool(images)
        has_files = bool(files)
        has_audio = bool(audio)
        
        memory = None
        # Use passed history or fallback to memory
        memory = None
        if history is None:
            history = []
            if thread_id:
                memory = MemoryManager(thread_id)
                history = memory.get_context_messages(limit=10)

        # Estimate prompt length for context-aware routing
        total_prompt_len = len(user_prompt) + len(system_prompt)
        if history:
            total_prompt_len += sum(len(m.get("content", "")) for m in history)

        model_list = self._get_ordered_model_list(preferred_provider, preferred_model, reasoning, prompt_len=total_prompt_len,
                                                   user_prompt=user_prompt, images=has_images, files=has_files,
                                                   audio=has_audio, tools=bool(tools or tool_choice), cost_mode=cost_mode)
        log.info(f"[ROUTER] Solicitud (stream): {len(model_list)} modelos candidatos.")

        # Circuit breaker: skip recently failed models with exponential backoff
        available_models = [
            m for m in model_list
            if self._is_available(f"{m['provider']}/{m['id']}")
        ]

        if not available_models and model_list:
            log.warning("[!] Todos los modelos en cooldown (stream). Forzando reintento con prioridad de velocidad.")
            from .config import PROVIDER_SPEED_PRIORITY
            p_map = {p: i for i, p in enumerate(PROVIDER_SPEED_PRIORITY)}
            model_list_sorted = sorted(model_list, key=lambda m: p_map.get(m.get("provider", "").lower(), 99))
            available_models = model_list_sorted[:10]

        # --- SMART SORT: sticky routing + EMA latency + cap candidates ---
        available_models = self._sort_candidates(available_models, thread_id)
        if len(available_models) > self.MAX_CANDIDATES:
            log.info(f"[ROUTER] Capando candidatos de {len(available_models)} a {self.MAX_CANDIDATES} (sticky + EMA sort).")
            available_models = available_models[:self.MAX_CANDIDATES]

        for model_info in available_models:
            provider_name = model_info["provider"]
            model_id = model_info["id"]
            capabilities = model_info["capabilities"]

            # Capability filtering
            start_time = time.time()
            circuit_key = self._circuit_key(provider_name, model_id)

            try:
                p_cfg = PROVIDERS.get(provider_name)
                api_key = os.getenv(p_cfg["env_key"]) if p_cfg["env_key"] else None
                if provider_name != "ollama" and not api_key:
                    continue

                enriched_prompt, shim_notice = self._prepare_context(
                    system_prompt, provider_name, files, user_prompt, reasoning
                )

                yield {"type": "metadata", "provider": provider_name, "model": model_id}

                if shim_notice:
                    yield {"type": "shim_notice", "chunk": shim_notice}

                full_response = ""
                tc_logged = False

                # ---- OpenAI-compatible ----
                if provider_name in ("github", "groq", "sambanova", "mistral", "openrouter", "cerebras", "cohere", "huggingface", "nvidia"):
                    stream = self._call_openai_style(
                        provider_name, model_id, p_cfg["base_url"], api_key,
                        enriched_prompt, user_prompt, images, history,
                        stream=True, tools=tools, tool_choice=tool_choice,
                        temperature=temperature, max_tokens=max_tokens,
                        response_format=response_format, parallel_tool_calls=parallel_tool_calls,
                        capabilities=capabilities,
                    )
                    for chunk in stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        content = delta.content or ""
                        reasoning = getattr(delta, "reasoning_content", None)
                        tool_calls = getattr(delta, "tool_calls", None)
                        if reasoning:
                            yield {"type": "reasoning", "chunk": reasoning}
                        if content:
                            if not full_response:
                                strategy_desc = "Estabilidad de Contexto" if total_prompt_len > 15000 else "Velocidad Estándar"
                                log.info(f"[SUCCESS] Ruteo: {preferred_model} -> {provider_name}/{model_id} (Estrategia: {strategy_desc})")
                            full_response += content
                            yield {"type": "content", "chunk": content}
                        if tool_calls:
                            # Forward function/tool call deltas to the SSE layer so
                            # agent clients (Hermes, Cursor, Continue) see them
                            # instead of receiving an empty stream.
                            serialized = []
                            for tc in tool_calls:
                                try:
                                    serialized.append(tc.model_dump(exclude_none=True))
                                except AttributeError:
                                    serialized.append(dict(tc) if hasattr(tc, "__iter__") else {"raw": str(tc)})
                            if not full_response and not tc_logged:
                                log.info(f"[SUCCESS] Ruteo (tool_calls): {preferred_model} -> {provider_name}/{model_id}")
                                tc_logged = True
                            yield {"type": "tool_calls", "chunk": serialized}

                # ---- Gemini ----
                elif provider_name == "gemini":
                    if not HAS_GEMINI:
                        yield {"type": "content", "chunk": "Error: SDK de Gemini no instalado."}
                        continue
                    stream = self._call_gemini(
                        model_id, api_key, enriched_prompt, user_prompt,
                        images, files, audio, history, stream=True
                    )
                    for chunk in stream:
                        if not chunk.candidates:
                            continue
                        for part in chunk.candidates[0].content.parts:
                            if hasattr(part, "thought") and part.thought:
                                yield {"type": "reasoning", "chunk": part.text}
                            elif part.text:
                                if not full_response:
                                    strategy_desc = "Estabilidad de Contexto" if total_prompt_len > 15000 else "Velocidad Estándar"
                                    log.info(f"[SUCCESS] Ruteo: {preferred_model} -> {provider_name}/{model_id} (Estrategia: {strategy_desc})")
                                full_response += part.text
                                yield {"type": "content", "chunk": part.text}

                # ---- Ollama ----
                elif provider_name == "ollama":
                    client = OllamaClient(host=p_cfg["base_url"])
                    messages = [{"role": "system", "content": enriched_prompt}]
                    if history:
                        messages.extend(history)
                    curr = {"role": "user", "content": user_prompt}
                    if images:
                        curr["images"] = [img.split(",")[-1] for img in images]
                    messages.append(curr)
                    for chunk in client.chat(model=model_id, messages=messages, stream=True):
                        msg = chunk.get("message", {}) or {}
                        c = msg.get("content", "")
                        tc = msg.get("tool_calls")
                        if c:
                            if not full_response:
                                strategy_desc = "Estabilidad de Contexto" if total_prompt_len > 15000 else "Velocidad Estándar"
                                log.info(f"[SUCCESS] Ruteo: {preferred_model} -> {provider_name}/{model_id} (Estrategia: {strategy_desc})")
                            full_response += c
                            yield {"type": "content", "chunk": c}
                        if tc:
                            # Ollama emits tool calls already as plain dicts.
                            yield {"type": "tool_calls", "chunk": tc}

                if thread_id and full_response:
                    try:
                        mem = MemoryManager(thread_id)
                        # Smart titling for new chats
                        history_count = len(mem.load_history())
                        if history_count == 0:
                            new_title = self.generate_chat_title(user_prompt)
                            mem.title = new_title
                            log.info(f"[MEMORY] Título generado: {new_title}")
                    except Exception as e_mem:
                        log.warning(f"[MEMORY] Error en gestión de memoria/título: {e_mem}")

                    # If retain_file_context is true, extract and append file text to user prompt
                    mem_user_prompt = user_prompt
                    if retain_file_context and files:
                        f_ctx, _ = FileProcessor.format_as_context(files, notify_shim=False)
                        if f_ctx:
                            mem_user_prompt += f"\n\n[CONTEXTO ADJUNTO GUARDADO EN MEMORIA]:\n{f_ctx}"

                    mem.save_message("user", mem_user_prompt)
                    mem.save_message("assistant", full_response)

                self._mark_success(circuit_key, (time.time() - start_time) * 1000, thread_id)
                return  # Success

            except Exception as e:
                err_msg = str(e).lower()
                ck = self._circuit_key(provider_name, model_id)
                if any(x in err_msg for x in ["429", "rate limit", "insufficient_quota", "overloaded"]):
                    self._mark_failure(ck, "rate_limit")
                elif any(x in err_msg for x in ["402", "403", "insufficient credits", "credit balance"]):
                    self._mark_failure(ck, "auth/credit")
                elif "404" in err_msg or "not found" in err_msg:
                    self._mark_failure(ck, "not_found")
                elif any(x in err_msg for x in ["413", "too large", "too many images"]):
                    self._mark_failure(ck, "payload_too_large")
                else:
                    log.warning(f"[STREAM] {provider_name}/{model_id}: {e}")
                    self._mark_failure(ck, f"unexpected: {type(e).__name__}")
                continue

        yield {"type": "content", "chunk": "ERROR: No se pudo obtener respuesta de ningun proveedor."}

    # ========================================================================
    # Synchronous Completion
    # ========================================================================

    def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[str] = None,
        files: List[Dict[str, str]] = None,
        audio: List[Dict[str, str]] = None,
        thread_id: str = None,
        preferred_provider: str = None,
        preferred_model: str = None,
        return_metadata: bool = False,
        reasoning: bool = False,
        retain_file_context: bool = False,
        tools: List[Dict[str, Any]] = None,
        tool_choice: Union[str, Dict[str, Any]] = None,
        history: List[Dict[str, Any]] = None,
        cost_mode: str = "free_only",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        parallel_tool_calls: Optional[bool] = None,
    ) -> Union[str, Tuple[str, str, str]]:
        # Auto-detect audio files
        files, audio = self._separate_audio_from_files(files, audio)
        
        has_images = bool(images)
        has_files = bool(files)
        has_audio = bool(audio)
        
        memory = None
        # Use passed history or fallback to memory
        if history is None:
            history = []
            if thread_id:
                memory = MemoryManager(thread_id)
                history = memory.get_context_messages(limit=10)

        # Estimate prompt length for context-aware routing
        total_prompt_len = len(user_prompt) + len(system_prompt)
        if history:
            total_prompt_len += sum(len(m.get("content", "")) for m in history)

        model_list = self._get_ordered_model_list(preferred_provider, preferred_model, reasoning, prompt_len=total_prompt_len,
                                                   user_prompt=user_prompt, images=has_images, files=has_files,
                                                   audio=has_audio, tools=bool(tools or tool_choice), cost_mode=cost_mode)
        log.info(f"[ROUTER] Solicitud (sync): {len(model_list)} modelos candidatos.")

        # Circuit breaker: skip recently failed models with exponential backoff
        available_models = [
            m for m in model_list
            if self._is_available(f"{m['provider']}/{m['id']}")
        ]

        if not available_models and model_list:
            log.warning("[!] Todos los modelos están en cooldown (sync). Forzando reintento con prioridad de velocidad.")
            from .config import PROVIDER_SPEED_PRIORITY
            p_map = {p: i for i, p in enumerate(PROVIDER_SPEED_PRIORITY)}
            model_list_sorted = sorted(model_list, key=lambda m: p_map.get(m.get("provider", "").lower(), 99))
            available_models = model_list_sorted[:10]

        # --- SMART SORT: sticky routing + EMA latency + cap candidates ---
        available_models = self._sort_candidates(available_models, thread_id)
        if len(available_models) > self.MAX_CANDIDATES:
            log.info(f"[ROUTER] Capando candidatos de {len(available_models)} a {self.MAX_CANDIDATES} (sticky + EMA sort).")
            available_models = available_models[:self.MAX_CANDIDATES]

        for model_info in available_models:
            provider_name = model_info["provider"]
            model_id = model_info["id"]
            capabilities = model_info["capabilities"]

            if has_images and VISION not in capabilities:
                continue
            if has_audio and AUDIO not in capabilities:
                continue
            if has_files and FILE not in capabilities and FILE_SHIM not in capabilities:
                continue

            start_time = time.time()
            circuit_key = self._circuit_key(provider_name, model_id)

            try:
                p_cfg = PROVIDERS.get(provider_name)
                api_key = os.getenv(p_cfg["env_key"]) if p_cfg["env_key"] else None
                if provider_name != "ollama" and not api_key:
                    continue

                enriched_prompt, _ = self._prepare_context(
                    system_prompt, provider_name, files, user_prompt, reasoning
                )

                res = ""
                if provider_name in ("github", "groq", "sambanova", "mistral", "openrouter", "cerebras", "cohere", "huggingface", "nvidia"):
                    res = self._call_openai_style(
                        provider_name, model_id, p_cfg["base_url"], api_key,
                        enriched_prompt, user_prompt, images, history, 
                        stream=False, tools=tools, tool_choice=tool_choice,
                        temperature=temperature, max_tokens=max_tokens,
                        response_format=response_format, parallel_tool_calls=parallel_tool_calls,
                        capabilities=capabilities,
                    )
                elif provider_name == "gemini":
                    if not HAS_GEMINI:
                        continue
                    res = self._call_gemini(
                        model_id, api_key, enriched_prompt, user_prompt,
                        images, files, audio, history, stream=False
                    )
                elif provider_name == "ollama":
                    res = self._call_ollama(
                        model_id, p_cfg["base_url"], enriched_prompt, user_prompt,
                        images, history
                    )

                tool_calls = None
                if isinstance(res, RouterResult):
                    tool_calls = res.tool_calls
                    res = res.content
                elif isinstance(res, dict):
                    tool_calls = res.get("tool_calls")
                    res = res.get("content") or ""
                if res or tool_calls:
                    log.info(f"[SUCCESS] {provider_name}/{model_id} completó la solicitud.")
                    if memory:
                        mem_user_prompt = user_prompt
                        if retain_file_context and files:
                            f_ctx, _ = FileProcessor.format_as_context(files, notify_shim=False)
                            if f_ctx:
                                mem_user_prompt += f"\n\n[CONTEXTO ADJUNTO GUARDADO EN MEMORIA]:\n{f_ctx}"
                        memory.save_message("user", mem_user_prompt)
                        memory.save_message("assistant", res)
                    self._mark_success(circuit_key, (time.time() - start_time) * 1000, thread_id)
                    if return_metadata:
                        result = RouterResult(content=res, tool_calls=tool_calls, finish_reason="tool_calls", provider=provider_name, model=model_id) if tool_calls else res
                        return result, provider_name, model_id
                    return res

            except Exception as e:
                err_msg = str(e).lower()
                ck = self._circuit_key(provider_name, model_id)
                if any(x in err_msg for x in ["429", "rate limit", "insufficient_quota", "overloaded"]):
                    self._mark_failure(ck, "rate_limit")
                elif any(x in err_msg for x in ["402", "403", "insufficient credits", "credit balance"]):
                    self._mark_failure(ck, "auth/credit")
                elif "404" in err_msg or "not found" in err_msg:
                    self._mark_failure(ck, "not_found")
                elif any(x in err_msg for x in ["413", "too large", "too many images"]):
                    self._mark_failure(ck, "payload_too_large")
                else:
                    log.warning(f"[ERR] {provider_name}/{model_id}: {e}")
                    self._mark_failure(ck, f"unexpected: {type(e).__name__}")
                continue

        err_res = "ERROR: Agotados todos los modelos. Verifica tus API keys y conexion."
        return (err_res, "none", "none") if return_metadata else err_res

    # ========================================================================
    # Fork / Parallel Mode — Ecosistema Gravedad
    # ========================================================================

    def _single_completion_call(
        self,
        model_info: Dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        images: List[str] = None,
        files: List[Dict[str, str]] = None,
        audio: List[Dict[str, str]] = None,
        history: List[Dict[str, Any]] = None,
        reasoning: bool = False,
    ) -> Dict[str, Any]:
        """Internal helper for fork mode: calls ONE model and returns structured result."""
        provider_name = model_info["provider"]
        model_id = model_info["id"]
        circuit_key = self._circuit_key(provider_name, model_id)
        start = time.time()

        try:
            p_cfg = PROVIDERS.get(provider_name)
            if not p_cfg:
                return {"provider": provider_name, "model": model_id, "ok": False, "error": "no config", "latency_ms": 0, "text": "", "score": 0}

            api_key = os.getenv(p_cfg["env_key"]) if p_cfg.get("env_key") else None
            if provider_name != "ollama" and not api_key:
                return {"provider": provider_name, "model": model_id, "ok": False, "error": "no key", "latency_ms": 0, "text": "", "score": 0}

            enriched_prompt, _ = self._prepare_context(system_prompt, provider_name, files, user_prompt, reasoning)

            res = ""
            if provider_name in ("github", "groq", "sambanova", "mistral", "openrouter", "cerebras", "cohere", "huggingface", "nvidia"):
                res = self._call_openai_style(
                    provider_name, model_id, p_cfg["base_url"], api_key,
                    enriched_prompt, user_prompt, images, history, stream=False
                )
            elif provider_name == "gemini":
                if not HAS_GEMINI:
                    return {"provider": provider_name, "model": model_id, "ok": False, "error": "gemini sdk missing", "latency_ms": 0, "text": "", "score": 0}
                res = self._call_gemini(
                    model_id, api_key, enriched_prompt, user_prompt,
                    images, files, audio, history, stream=False
                )
            elif provider_name == "ollama":
                res = self._call_ollama(
                    model_id, p_cfg["base_url"], enriched_prompt, user_prompt,
                    images, history
                )

            latency_ms = (time.time() - start) * 1000
            if res and not res.startswith("ERROR") and len(res.strip()) > 10:
                self._mark_success(circuit_key, latency_ms)
                # Simple quality score: penalize very short, reward moderate length, slight speed bonus
                text_len = len(res.strip())
                score = min(text_len, 2000)  # cap length score
                score += max(0, 500 - latency_ms) * 0.1  # speed bonus up to 500ms
                return {
                    "provider": provider_name,
                    "model": model_id,
                    "ok": True,
                    "error": None,
                    "latency_ms": round(latency_ms, 1),
                    "text": res,
                    "score": round(score, 1),
                }
            else:
                return {"provider": provider_name, "model": model_id, "ok": False, "error": "empty or error response", "latency_ms": round(latency_ms, 1), "text": res, "score": 0}

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            self._mark_failure(circuit_key, f"fork_error: {type(e).__name__}")
            return {"provider": provider_name, "model": model_id, "ok": False, "error": str(e)[:120], "latency_ms": round(latency_ms, 1), "text": "", "score": 0}

    def fork_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        images: List[str] = None,
        files: List[Dict[str, str]] = None,
        audio: List[Dict[str, str]] = None,
        thread_id: str = None,
        preferred_provider: str = None,
        preferred_model: str = None,
        reasoning: bool = False,
        max_parallel: int = 3,
        return_all: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Modo Fork del ecosistema Gravedad: ejecuta múltiples modelos en paralelo
        para la MISMA tarea, compara resultados y devuelve el mejor (o todos).

        Args:
            max_parallel: Cuántos modelos lanzar simultáneamente (diferentes providers)
            return_all: Si True, devuelve lista con TODOS los resultados ordenados por score

        Returns:
            Si return_all=False: dict del mejor resultado (campos: provider, model, text, latency_ms, score, others)
            Si return_all=True: lista de dicts ordenada por score descendente
        """
        model_list = self._get_ordered_model_list(
            preferred_provider, preferred_model, reasoning,
            prompt_len=len(user_prompt) + len(system_prompt)
        )

        # Filtrar disponibles y diversificar providers (no repetir mismo provider)
        available_models = [
            m for m in model_list
            if self._is_available(f"{m['provider']}/{m['id']}")
        ]

        # De-duplicar por provider para máxima diversidad
        seen_providers = set()
        diverse_models = []
        for m in available_models:
            prov = m["provider"]
            if prov not in seen_providers:
                seen_providers.add(prov)
                diverse_models.append(m)
        # Si hay poca diversidad, rellenar con otros modelos del mismo provider
        if len(diverse_models) < max_parallel:
            for m in available_models:
                if m not in diverse_models and len(diverse_models) < max_parallel:
                    diverse_models.append(m)

        candidates = diverse_models[:max_parallel]
        if not candidates:
            return {"provider": "none", "model": "none", "text": "ERROR: Sin modelos disponibles para fork.", "score": 0}

        log.info(f"[FORK] Lanzando {len(candidates)} modelos en paralelo: { [m['provider'] + '/' + m['id'] for m in candidates] }")

        results: List[Dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            future_to_model = {
                executor.submit(
                    self._single_completion_call,
                    m, system_prompt, user_prompt, images, files, audio, None, reasoning
                ): m
                for m in candidates
            }
            for future in concurrent.futures.as_completed(future_to_model):
                result = future.result()
                results.append(result)
                status = "OK" if result["ok"] else f"FAIL({result.get('error','')})"
                log.info(f"[FORK] {result['provider']}/{result['model']}: {status} | {result['latency_ms']}ms | score={result['score']}")

        # Ordenar por score descendente, luego ok primero
        results.sort(key=lambda r: (r["ok"], r["score"]), reverse=True)

        if return_all:
            return results

        winner = results[0] if results else {"provider": "none", "model": "none", "text": "", "score": 0}
        if not winner["ok"] and len(results) > 1:
            # Si el primero falló, buscar el primer ok
            for r in results:
                if r["ok"]:
                    winner = r
                    break

        winner["others"] = [r for r in results if r != winner]
        log.info(f"[FORK] WINNER: {winner['provider']}/{winner['model']} (score={winner['score']}, latency={winner['latency_ms']}ms)")
        return winner

    # ========================================================================
    # Provider Calls
    # ========================================================================

    def _call_openai_style(self, provider, model, base_url, api_key,
                           system_prompt, user_prompt, images, history, 
                           stream=False, tools=None, tool_choice=None,
                           temperature=None, max_tokens=None, response_format=None,
                           parallel_tool_calls=None, capabilities=None):
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=self.REQUEST_TIMEOUT_SECONDS)
        # For strict providers (like NVIDIA), if no images are present, send content as string
        if not images:
            user_msg_content = user_prompt
        else:
            current_content = [{"type": "text", "text": user_prompt}]
            # Handle provider-specific image limits (e.g. Groq supports max 5)
            effective_images = images
            if provider == "groq" and len(images) > 5:
                log.info(f"[VISION-LIMIT] {provider}/{model} solo admite 5 imágenes. Recortando de {len(images)} a 5.")
                effective_images = images[:5]
                
            for img_b64 in effective_images:
                img_src = f"data:image/jpeg;base64,{img_b64}" if not img_b64.startswith("data:") else img_b64
                current_content.append({"type": "image_url", "image_url": {"url": img_src}})
            user_msg_content = current_content

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_msg_content})
        
        # Tool-calling responses must fit: (a) the model's chain-of-thought
        # prose, (b) the full JSON envelope of every tool invocation
        # (name + arguments — web_search snippets in particular blow up),
        # plus (c) the assistant's final answer. Smaller models (Ministral
        # 14B, Nemotron Nano) are verbose enough to truncate at 8192 mid
        # tool-call, leaving partial JSON that the client (Hermes) rejects
        # with "incomplete tool arguments" and that poisons history with
        # `function.name = ""`. 16384 is comfortably under Ministral 14B's
        # 128k context window and stops the truncation in practice.
        effective_max_tokens = max_tokens or (16384 if tools else 4096)
        create_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": effective_max_tokens,
            "temperature": 0.7 if temperature is None else temperature,
            "stream": stream,
        }
        if tools:
            create_kwargs["tools"] = tools
            if tool_choice:
                create_kwargs["tool_choice"] = tool_choice
            if parallel_tool_calls is not None and "parallel_tools" in (capabilities or []):
                create_kwargs["parallel_tool_calls"] = parallel_tool_calls
        if response_format and "structured_output" in (capabilities or []):
            create_kwargs["response_format"] = response_format

        response = client.chat.completions.create(**create_kwargs)
        if stream:
            return response
        message = response.choices[0].message
        if tools and getattr(message, "tool_calls", None):
            calls = []
            for call in message.tool_calls:
                try:
                    calls.append(call.model_dump(exclude_none=True))
                except AttributeError:
                    calls.append(dict(call))
            usage = response.usage.model_dump(exclude_none=True) if getattr(response, "usage", None) else None
            return RouterResult(content=message.content or "", tool_calls=calls, finish_reason="tool_calls", usage=usage, provider=provider, model=model)
        return message.content

    def _call_gemini(self, model_id, api_key, system_prompt, user_prompt,
                     images_b64, files_data, audio_data, history, stream=False):
        # Cache client to prevent 'httpx connection closed' due to garbage collection mid-stream
        client_key = f"gemini_{api_key}"
        if client_key not in self.clients:
            self.clients[client_key] = genai.Client(api_key=api_key)
        client = self.clients[client_key]

        contents = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        prompt_parts = [types.Part.from_text(text=user_prompt)]

        if images_b64:
            for b64 in images_b64:
                img_data = base64.b64decode(b64.split(",")[-1])
                prompt_parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))

        if files_data:
            for f in files_data:
                try:
                    f_data = base64.b64decode(f["data"].split(",")[-1])
                    prompt_parts.append(types.Part.from_bytes(
                        data=f_data, mime_type=f.get("mime_type", "application/octet-stream")
                    ))
                except Exception as e:
                    log.warning(f"Gemini file error: {e}")

        if audio_data:
            for a in audio_data:
                try:
                    a_data = base64.b64decode(a["data"].split(",")[-1])
                    prompt_parts.append(types.Part.from_bytes(
                        data=a_data, mime_type=a.get("mime_type", "audio/webm")
                    ))
                except Exception as e:
                    log.warning(f"Gemini audio error: {e}")

        contents.append(types.Content(role="user", parts=prompt_parts))
        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="BLOCK_NONE"),
            ]
        )

        try:
            if stream:
                return client.models.generate_content_stream(model=model_id, contents=contents, config=gen_config)
            response = client.models.generate_content(model=model_id, contents=contents, config=gen_config)
            
            # Si Gemini bloqueó la respuesta, response.text fallará o estará vacío
            if not response.text:
                raise ValueError("Gemini response is empty (possible safety block)")
            
            # Detectar respuestas que son solo JSON de seguridad (frecuente en fallos de SDK)
            if '{"User Safety":' in response.text or '{"Response Safety":' in response.text:
                raise ValueError("Gemini returned safety metadata instead of content")
                
            return response.text
        except Exception as e:
            log.warning(f"[GEMINI-ERROR] {model_id} bloqueado o falló: {e}")
            raise e

    def _call_ollama(self, model, host, system_prompt, user_prompt, images, history):
        client = OllamaClient(host=host)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        current_message = {"role": "user", "content": user_prompt}
        if images:
            current_message["images"] = [img.split(",")[-1] for img in images]
        messages.append(current_message)
        response = client.chat(model=model, messages=messages)
        return response.get("message", {}).get("content", "").strip()

    # ========================================================================
    # Text-to-Speech (TTS)
    # ========================================================================

    @staticmethod
    async def text_to_speech(
        text: str,
        voice: str = "es-MX-DaliaNeural",
        output_path: str = None,
    ) -> Optional[str]:
        """
        Convert text to speech using edge-tts (free, no API key needed).
        Returns path to the generated audio file.
        Available voices: es-MX-DaliaNeural, es-MX-JorgeNeural,
                         en-US-JennyNeural, en-US-GuyNeural, etc.
        """
        try:
            import edge_tts
            import tempfile

            if not output_path:
                temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
                os.makedirs(temp_dir, exist_ok=True)
                output_path = os.path.join(temp_dir, f"tts_{int(__import__('time').time())}.mp3")

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            log.info(f"[TTS] Generated: {output_path}")
            return output_path
        except ImportError:
            log.error("[TTS] edge-tts not installed. Run: pip install edge-tts")
            return None
        except Exception as e:
            log.error(f"[TTS] Error: {e}")
            return None

    @staticmethod
    def get_tts_voices() -> List[Dict[str, str]]:
        """Return a curated list of available TTS voices."""
        return [
            {"id": "es-MX-DaliaNeural", "name": "Dalia (Español MX)", "lang": "es"},
            {"id": "es-MX-JorgeNeural", "name": "Jorge (Español MX)", "lang": "es"},
            {"id": "es-ES-ElviraNeural", "name": "Elvira (Español ES)", "lang": "es"},
            {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Español ES)", "lang": "es"},
            {"id": "es-CO-SalomeNeural", "name": "Salome (Español CO)", "lang": "es"},
            {"id": "en-US-JennyNeural", "name": "Jenny (English US)", "lang": "en"},
            {"id": "en-US-GuyNeural", "name": "Guy (English US)", "lang": "en"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (English UK)", "lang": "en"},
            {"id": "fr-FR-DeniseNeural", "name": "Denise (Français)", "lang": "fr"},
            {"id": "pt-BR-FranciscaNeural", "name": "Francisca (Português BR)", "lang": "pt"},
            {"id": "ja-JP-NanamiNeural", "name": "Nanami (日本語)", "lang": "ja"},
            {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao (中文)", "lang": "zh"},
        ]

    # ========================================================================
    # Image Generation
    # ========================================================================

    def generate_image(
        self,
        prompt: str,
        provider: str = "gemini",
        model: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an image from a text prompt.
        Supports Gemini, Pollinations, HuggingFace, NVIDIA, Ollama, and OpenAI-style.
        Includes automatic fallback to Pollinations if primary provider fails.
        """
        result = None
        
        # Determine how to call the provider
        if provider == "gemini":
            result = self._generate_image_gemini(prompt, model)
        elif provider == "pollinations":
            result = self._generate_image_pollinations(prompt, model)
        elif provider == "huggingface":
            result = self._generate_image_huggingface(prompt, model)
        elif provider == "nvidia":
            result = self._generate_image_nvidia(prompt, model)
        elif provider == "ollama":
            result = self._generate_image_ollama(prompt, model)
        elif provider in ("openrouter", "github"):
            result = self._generate_image_openai_style(prompt, provider, model)
            
        # Fallback to Pollinations if it failed and we aren't already using it
        if not result and provider != "pollinations":
            log.warning(f"[IMGGEN] Primary provider ({provider}) failed. Falling back to Pollinations.")
            result = self._generate_image_pollinations(prompt, "flux")
            
        return result

    def _generate_image_gemini(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate image using Gemini's Imagen model."""
        if not HAS_GEMINI:
            log.error("[IMGGEN] Gemini SDK not installed.")
            return None
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            log.error("[IMGGEN] GEMINI_API_KEY not set.")
            return None
        try:
            client_key = f"gemini_{api_key}"
            if client_key not in self.clients:
                self.clients[client_key] = genai.Client(api_key=api_key)
            client = self.clients[client_key]

            # Use dedicated generate_images method with Imagen
            target_model = model or "imagen-4.0-generate-001"
            response = client.models.generate_images(
                model=target_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                ),
            )

            if not response.generated_images:
                log.warning(f"[IMGGEN] No images in Gemini response ({target_model}).")
                return None

            gen_img = response.generated_images[0]
            img_data = gen_img.image.data
            mime = gen_img.image.mime_type or "image/png"
            
            temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
            os.makedirs(temp_dir, exist_ok=True)
            
            ext = mime.split("/")[-1] if "/" in mime else "png"
            filename = f"img_{int(__import__('time').time())}.{ext}"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_data)
            
            log.info(f"[IMGGEN] Generated: {filepath} using {target_model}")
            return {
                "path": filepath,
                "filename": filename,
                "mime_type": mime,
                "b64_data": base64.b64encode(img_data).decode(),
            }
        except Exception as e:
            log.error(f"[IMGGEN] Gemini error: {e}")
            return None

    def _generate_image_pollinations(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate image using Pollinations AI (Free, No Key)."""
        import requests
        import urllib.parse
        try:
            # Pollinations uses a simple GET URL
            # Models: flux, flux-realism, any-dark, etc.
            p_model = model or "flux"
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={p_model}&width=1024&height=1024&seed={int(__import__('time').time())}&nologo=true"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                img_data = response.content
                temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
                os.makedirs(temp_dir, exist_ok=True)
                filename = f"img_poll_{int(__import__('time').time())}.png"
                filepath = os.path.join(temp_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                log.info(f"[IMGGEN] Generated via Pollinations: {filepath}")
                return {
                    "path": filepath,
                    "filename": filename,
                    "mime_type": "image/png",
                    "b64_data": base64.b64encode(img_data).decode(),
                }
            else:
                log.error(f"[IMGGEN] Pollinations error: {response.status_code}")
                return None
        except Exception as e:
            log.error(f"[IMGGEN] Pollinations internal error: {e}")
            return None

    def _generate_image_huggingface(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate image using Hugging Face Inference API."""
        import requests
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            log.warning("[IMGGEN] HUGGINGFACE_API_KEY not set. Attempting without auth (may fail).")
            
        try:
            target_model = model or "black-forest-labs/FLUX.1-schnell"
            url = f"https://router.huggingface.co/hf-inference/models/{target_model}"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {"inputs": prompt}
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                img_data = response.content
                temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
                os.makedirs(temp_dir, exist_ok=True)
                filename = f"img_hf_{int(__import__('time').time())}.png"
                filepath = os.path.join(temp_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                
                log.info(f"[IMGGEN] Generated via HF ({target_model}): {filepath}")
                return {
                    "path": filepath,
                    "filename": filename,
                    "mime_type": "image/png",
                    "b64_data": base64.b64encode(img_data).decode(),
                }
            else:
                log.error(f"[IMGGEN] HF error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            log.error(f"[IMGGEN] HF internal error: {e}")
            return None

    def _generate_image_ollama(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate image using Ollama (Local Experimental)."""
        try:
            # We use the 'ollama' package but the generate call is different for images
            # Currently Ollama's python SDK might not have a clean 'generate_image' yet
            # so we use a direct request to the local API
            import requests
            target_model = model or "flux2-klein:4b"
            url = f"{PROVIDERS['ollama']['base_url']}/api/generate"
            
            # NOTE: Image generation in Ollama is highly experimental and might change
            payload = {
                "model": target_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code == 200:
                data = response.json()
                # Ollama often returns the base64 or a path in the response for images
                # This depends on the specific model implementation in Ollama
                # For FLUX in Ollama, it often outputs the raw image bytes in the 'response' or similar
                # [ADJ] Based on common experimental implementations:
                if "response" in data:
                    # In some versions, the response IS the base64 or contains the path
                    return None # placeholder until stable
            log.warning("[IMGGEN] Ollama image generation is still too unstable/experimental for production.")
            return None
        except Exception as e:
            log.error(f"[IMGGEN] Ollama image error: {e}")
            return None

    def _generate_image_openai_style(self, prompt: str, provider: str, model: str = None) -> Optional[Dict]:
        """Generate image using an OpenAI-compatible images API."""
        p_cfg = PROVIDERS.get(provider)
        if not p_cfg:
            return None
        api_key = os.getenv(p_cfg["env_key"])
        if not api_key:
            return None
        try:
            client = OpenAI(base_url=p_cfg["base_url"], api_key=api_key)
            response = client.images.generate(
                model=model or "dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            image_url = response.data[0].url
            # Download the image
            import urllib.request
            temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
            os.makedirs(temp_dir, exist_ok=True)
            filename = f"img_{int(__import__('time').time())}.png"
            filepath = os.path.join(temp_dir, filename)
            urllib.request.urlretrieve(image_url, filepath)
            with open(filepath, "rb") as f:
                img_data = f.read()
            log.info(f"[IMGGEN] Generated: {filepath}")
            return {
                "path": filepath,
                "filename": filename,
                "mime_type": "image/png",
                "b64_data": base64.b64encode(img_data).decode(),
            }
        except Exception as e:
            log.error(f"[IMGGEN] {provider} error: {e}")
            return None

    # ---- NVIDIA NIM Image Generation ----
    # NVIDIA uses a separate domain (ai.api.nvidia.com) with per-model endpoints.
    # Supported: SDXL, FLUX.1-dev, FLUX.1-schnell

    NVIDIA_IMG_MODELS = {
        "sdxl": {
            "url": "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl",
            "format": "sdxl",
            "name": "Stable Diffusion XL",
        },
        "flux.1-dev": {
            "url": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev",
            "format": "flux",
            "name": "FLUX.1 Dev",
        },
        "flux.1-schnell": {
            "url": "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell",
            "format": "flux",
            "name": "FLUX.1 Schnell",
        },
    }

    def _generate_image_nvidia(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate image using NVIDIA NIM image endpoints (SDXL, FLUX)."""
        import requests
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            log.error("[IMGGEN] NVIDIA_API_KEY not set.")
            return None

        target = model or "sdxl"
        model_cfg = self.NVIDIA_IMG_MODELS.get(target)
        if not model_cfg:
            log.warning(f"[IMGGEN] Unknown NVIDIA image model: {target}. Falling back to SDXL.")
            model_cfg = self.NVIDIA_IMG_MODELS["sdxl"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Build payload based on format
        if model_cfg["format"] == "sdxl":
            payload = {
                "text_prompts": [{"text": prompt, "weight": 1}],
                "seed": int(__import__('time').time()) % 1000000,
                "steps": 25,
                "cfg_scale": 5,
                "height": 1024,
                "width": 1024,
            }
        else:  # flux format
            steps = 4 if "schnell" in target else 25
            payload = {
                "prompt": prompt,
                "seed": int(__import__('time').time()) % 1000000,
                "steps": steps,
                "height": 1024,
                "width": 1024,
            }

        try:
            response = requests.post(
                model_cfg["url"], json=payload, headers=headers, timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                artifacts = data.get("artifacts", [])
                if artifacts and artifacts[0].get("base64"):
                    b64_data = artifacts[0]["base64"]
                    img_data = base64.b64decode(b64_data)

                    temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
                    os.makedirs(temp_dir, exist_ok=True)
                    filename = f"img_nv_{int(__import__('time').time())}.png"
                    filepath = os.path.join(temp_dir, filename)

                    with open(filepath, "wb") as f:
                        f.write(img_data)

                    log.info(f"[IMGGEN] NVIDIA ({model_cfg['name']}): {filepath}")
                    return {
                        "path": filepath,
                        "filename": filename,
                        "mime_type": "image/png",
                        "b64_data": b64_data,
                    }
                else:
                    log.warning(f"[IMGGEN] NVIDIA: No artifacts in response.")
            else:
                log.error(f"[IMGGEN] NVIDIA HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            log.error(f"[IMGGEN] NVIDIA error: {e}")
        return None

    # ========================================================================
    # Video Generation
    # ========================================================================

    def generate_video(
        self,
        prompt: str,
        provider: str = "gemini",
        model: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a video from a text prompt using Gemini Veo.
        Returns: {"path": str, "filename": str, "mime_type": str} or None.
        """
        if provider == "gemini":
            return self._generate_video_gemini(prompt, model)
        elif provider == "huggingface_space":
            return self._generate_video_hf_space(prompt)
        log.error(f"[VIDGEN] Unsupported provider: {provider}")
        return None

    def _generate_video_hf_space(self, prompt: str) -> Optional[Dict]:
        """Generate video using Hugging Face Spaces hack via gradio_client."""
        try:
            from gradio_client import Client  # type: ignore[import-not-found]
        except ImportError:
            raise Exception("La librería gradio_client no está instalada en el backend.")

        import uuid
        import shutil
        
        # We try a very permissive spaces config without token (anonymous).
        # We use known popular models. The user is warned it might fail.
        spaces = [
            ("multimodalart/LTX-Video", "predict", {"prompt": prompt, "negative_prompt": "low quality", "image": None, "seed": 0, "num_inference_steps": 30, "guidance_scale": 7.5}),
            ("tencent/HunyuanVideo", "predict", {"prompt": prompt}),
        ]
        
        for space_id, api_name, payload in spaces:
            try:
                log.info(f"Intentando generar video gratis en {space_id}...")
                client = Client(space_id) 
                
                # We do dynamic unpacking just in case it takes direct args
                args = list(payload.values())
                result = client.predict(*args, api_name=api_name)
                
                # Result usually is a file path or a dict with 'video'
                video_path = None
                if isinstance(result, str) and result.endswith('.mp4'):
                    video_path = result
                elif isinstance(result, tuple) and len(result) > 0 and isinstance(result[0], dict) and 'video' in result[0]:
                    video_path = result[0]['video']
                elif isinstance(result, dict) and 'video' in result:
                    video_path = result['video']
                elif isinstance(result, tuple) and isinstance(result[0], str) and result[0].endswith('.mp4'):
                    video_path = result[0]
                
                if video_path and os.path.exists(video_path):
                    # Copy to our temp directory
                    safe_filename = f"hf_vid_{uuid.uuid4().hex[:8]}.mp4"
                    dst = os.path.join(TEMP_MEDIA_DIR, safe_filename)
                    os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)
                    shutil.copy(video_path, dst)
                    return {
                        "path": dst,
                        "filename": safe_filename,
                        "mime_type": "video/mp4"
                    }
            except Exception as e:
                log.warning(f"Fallo en space {space_id}: {e}")
                continue
                
        raise Exception("Las colas gratuitas de Hugging Face están saturadas o nos han bloqueado. Por favor, intenta de nuevo más tarde o usa Gemini.")

    def _generate_video_gemini(self, prompt: str, model: str = None) -> Optional[Dict]:
        """Generate video using Gemini Veo model."""
        if not HAS_GEMINI:
            return None
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import time as _time
            client_key = f"gemini_{api_key}"
            if client_key not in self.clients:
                self.clients[client_key] = genai.Client(api_key=api_key)
            client = self.clients[client_key]

            # Use Veo for video generation
            operation = client.models.generate_video(
                model=model or "veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    person_generation="allow_all",
                    number_of_videos=1,
                ),
            )

            # Poll until done (max 5 minutes)
            max_wait = 300
            waited = 0
            while not operation.done and waited < max_wait:
                _time.sleep(10)
                waited += 10
                operation = client.operations.get(name=operation.name)

            if not operation.done:
                log.error("[VIDGEN] Video generation timed out.")
                return None

            result = operation.result
            if result and result.generated_videos:
                video = result.generated_videos[0].video
                if video and video.uri:
                    # Download the video
                    temp_dir = os.path.join(os.path.dirname(__file__), "temp_media")
                    os.makedirs(temp_dir, exist_ok=True)
                    filename = f"vid_{int(_time.time())}.mp4"
                    filepath = os.path.join(temp_dir, filename)
                    
                    import urllib.request
                    urllib.request.urlretrieve(video.uri, filepath)
                    log.info(f"[VIDGEN] Generated: {filepath}")
                    return {
                        "path": filepath,
                        "filename": filename,
                        "mime_type": "video/mp4",
                    }
            log.warning("[VIDGEN] No video in response.")
            return None
        except Exception as e:
            log.error(f"[VIDGEN] Gemini error: {e}")
            return None
