# ai_services/config.py
"""
Provider definitions and capability constants for the AI Router.
The MODELS_REGISTRY is populated dynamically at startup by model_fetcher.py.
"""

# --- Capability Flags ---
# Model type / purpose
TEXT = "text"              # Standard chat/completion LLM
VISION = "vision"          # Can process images
AUDIO = "audio"            # Can process audio input (mic or file)
FILE = "file"              # Can process documents/files natively
FILE_SHIM = "file_shim"    # Can process docs via text injection (not native)
REASONING = "reasoning"    # Has chain-of-thought / thinking capability
MOE = "moe"                # Mixture of Experts architecture
CODE = "code"              # Optimized for code generation
EMBEDDING = "embedding"    # Text/image embedding model (not for chat)
RERANK = "rerank"          # Reranking model (not for chat)
TTS = "tts"                # Text-to-speech model
IMAGE_GEN = "image_gen"    # Image generation model
VIDEO_GEN = "video_gen"    # Video generation model
FREE = "free"              # Available at no cost
RAPIDO = "rapido"
STANDARD = "standard"
RAZONAMIENTO = "razonamiento"
AGENTICO = "agentico"      # Strong multi-step tool callers (Claude Sonnet+, GPT-4o+, Llama 3.3 70B, ...)
VISTA = "vista"            # Free vision-capable models (multimodal text+image)
AUTO = "auto"

# Categories that indicate a model is NOT suitable for chat
NON_CHAT_TYPES = {EMBEDDING, RERANK, TTS, IMAGE_GEN, VIDEO_GEN, "asr"}

# ---------------------------------------------------------------------------
# Strong-tool-caller heuristic — used by the AGENTICO tier.
# Conservative pattern list of model families empirically reliable at
# multi-step tool-calling sequences (i.e. invoking the same/different tool
# several times within one assistant turn without dropping calls, hallucinating
# tool names, or merging arguments).
# Keep this list curated; do NOT auto-expand from provider metadata. The whole
# point of this tier is "models that agents can trust" — false positives
# defeat the purpose.
# ---------------------------------------------------------------------------
import re as _re_tools

_STRONG_TOOL_CALLER_RE = _re_tools.compile(
    r"("
    r"claude-(sonnet|opus)-([3-9]|\d{2,})"    # Claude Sonnet/Opus 3.x and 4.x+
    r"|gpt-(4o|4\.1|5|6)"                     # GPT-4o, 4.1, 5+
    r"|gemini-(2\.5|3|4)"                     # Gemini 2.5+
    r"|gemini-2\.0-flash"                     # Gemini 2.0 Flash (proven baseline)
    r"|llama-3\.3-70b"                        # Llama 3.3 70B
    r"|llama-3\.1-405b"                       # Llama 3.1 405B
    r"|llama-(4|5)"                           # Llama 4+
    r"|qwen-?2\.5-(72b|110b)"                 # Qwen 2.5 large
    r"|qwen-?3"                               # Qwen 3+
    r"|mistral-(large|medium)"                # Mistral Large/Medium
    r"|magistral"                             # Magistral
    r"|deepseek-v3"                           # DeepSeek V3
    r"|deepseek-r1"                           # DeepSeek R1
    r"|command-r-plus"                        # Cohere Command R+
    r"|grok-(3|4|5)"                          # xAI Grok 3+
    r")",
    _re_tools.IGNORECASE,
)


def is_strong_tool_caller(model_id: str) -> bool:
    """True for models proven reliable at multi-step tool-calling sequences.

    Used by the AGENTICO virtual tier to filter the catalog to models an
    agent can trust for `tools` calls. Pattern-based so future minor versions
    (e.g. Claude Sonnet 5) match without code changes; major-family additions
    (a new vendor) require updating `_STRONG_TOOL_CALLER_RE` above.
    """
    return bool(_STRONG_TOOL_CALLER_RE.search(model_id or ""))

# --- Provider Configuration ---
PROVIDERS = {
    "github": {
        "base_url": "https://models.inference.ai.azure.com",
        "env_key": "GITHUB_TOKEN",
        "supports_vision": True,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "supports_vision": True,
        "supports_audio": True,
        "supports_files_native": False,
    },
    "sambanova": {
        "base_url": "https://api.sambanova.ai/v1",
        "env_key": "SAMBANOVA_API_KEY",
        "supports_vision": True,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "env_key": "MISTRAL_API_KEY",
        "supports_vision": True,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "supports_vision": True,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "gemini": {
        "base_url": None,
        "env_key": "GEMINI_API_KEY",
        "supports_vision": True,
        "supports_audio": True,
        "supports_files_native": True,
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "supports_vision": False,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "cohere": {
        "base_url": "https://api.cohere.ai/compatibility/v1",
        "env_key": "COHERE_API_KEY",
        "supports_vision": False,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "ollama": {
        "base_url": "http://127.0.0.1:11434",
        "env_key": None,
        "supports_vision": True,
        "supports_audio": False,
        "supports_files_native": False,
    },
    "pollinations": {
        "base_url": "https://image.pollinations.ai",
        "env_key": None,
        "requires_auth": False,
    },
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co/v1",
        "env_key": "HUGGINGFACE_API_KEY",
        "requires_auth": True,
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "env_key": "NVIDIA_API_KEY",
        "supports_vision": True,
        "supports_audio": True,
        "supports_files_native": False,
    }
}

# --- Provider Speed Tiers (fastest first for priority ordering) ---
# Used by the router to prefer faster providers when no specific model is chosen.
PROVIDER_SPEED_PRIORITY = [
    "cerebras",    # Ultra-fast inference
    "groq",        # Very fast
    "nvidia",      # NVIDIA NIMs (very fast)
    "sambanova",   # Fast
    "gemini",      # Fast + multimodal
    "github",      # Good speed, limited models
    "huggingface", # Depends on the exact Space/API, generally good
    "ollama",      # Local (depends on hardware)
    "openrouter",  # Aggregator, varies
    "mistral",     # Medium speed
    "cohere",      # Medium speed
]

# ============================================================================
# Provider Metadata & Operational Limits
# ============================================================================
# Used by the router and API clients to know EXACTLY what a model can do.

PROVIDER_METADATA = {
    "github": {
        "max_images_per_request": 10,
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 128000,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "groq": {
        "max_images_per_request": 5,
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 8192,
        "supports_reasoning_stream": False,
        "supports_audio_input": True,  # Whisper / transcription
        "supports_native_files": False,
        "pricing": "free",
        "input_modalities": ["text", "image", "audio"],
        "output_modalities": ["text"],
    },
    "sambanova": {
        "max_images_per_request": None,  # Varies by model, usually 10
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 4096,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "mistral": {
        "max_images_per_request": None,
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 128000,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "mixed",  # small/medium/pixtral have free tier, large/codestral are paid
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "openrouter": {
        "max_images_per_request": None,  # Depends on underlying provider
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 200000,
        "supports_reasoning_stream": True,  # Some models do
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "mixed",  # free + paid
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
    },
    "gemini": {
        "max_images_per_request": 1000,  # Very high, practically unlimited
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 1000000,
        "supports_reasoning_stream": True,
        "supports_audio_input": True,
        "supports_native_files": True,   # PDF, video, etc.
        "pricing": "mixed",  # Flash/Lite are free-tier generous, Pro has limits
        "input_modalities": ["text", "image", "audio", "video", "pdf"],
        "output_modalities": ["text", "image", "video"],
    },
    "cerebras": {
        "max_images_per_request": 0,
        "supports_tools": False,
        "supports_streaming": True,
        "max_context_hint": 8192,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "cohere": {
        "max_images_per_request": 0,
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 128000,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",  # Generous trial/free tier via compat API
        "input_modalities": ["text"],
        "output_modalities": ["text"],
    },
    "ollama": {
        "max_images_per_request": 10,  # Depends on model
        "supports_tools": False,  # Most don't, some new do
        "supports_streaming": True,
        "max_context_hint": 128000,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",  # Local = free
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "image"],
    },
    "pollinations": {
        "max_images_per_request": 0,
        "supports_tools": False,
        "supports_streaming": False,
        "max_context_hint": 0,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",
        "input_modalities": ["text"],
        "output_modalities": ["image"],
    },
    "huggingface": {
        "max_images_per_request": 1,  # Inference API limited
        "supports_tools": False,
        "supports_streaming": False,
        "max_context_hint": 4096,
        "supports_reasoning_stream": False,
        "supports_audio_input": False,
        "supports_native_files": False,
        "pricing": "free",  # Serverless inference is free tier
        "input_modalities": ["text", "image"],
        "output_modalities": ["text", "image"],
    },
    "nvidia": {
        "max_images_per_request": 10,
        "supports_tools": True,
        "supports_streaming": True,
        "max_context_hint": 128000,
        "supports_reasoning_stream": False,
        "supports_audio_input": True,
        "supports_native_files": False,
        "pricing": "free",  # Free tier exists
        "input_modalities": ["text", "image", "audio"],
        "output_modalities": ["text", "image"],
    },
}


# --- Context Window Heuristics ---
# Maps model name patterns to approximate context windows.
# Order matters: more specific patterns first.
_CONTEXT_WINDOW_RULES = [
    # Gemini
    ("gemini-2.5-pro", 1000000),
    ("gemini-2.0-flash", 1000000),
    ("gemini-1.5-pro", 2000000),
    ("gemini-1.5-flash", 1000000),
    ("gemini-1.0-pro", 32000),
    # GPT
    ("gpt-4.1", 1000000),
    ("gpt-4o", 128000),
    ("gpt-4-turbo", 128000),
    ("gpt-4", 128000),  # careful, catches gpt-4o too, but placed after
    ("gpt-3.5-turbo", 16000),
    # Claude
    ("claude-3-opus", 200000),
    ("claude-3-5-sonnet", 200000),
    ("claude-3-sonnet", 200000),
    ("claude-3-haiku", 200000),
    # Llama
    ("llama-3.3-70b", 128000),
    ("llama-3.2-90b", 128000),
    ("llama-3.2-11b", 128000),
    ("llama-3.1-70b", 128000),
    ("llama-3.1-8b", 128000),
    ("llama-3.1-405b", 128000),
    ("llama-3-70b", 8192),
    ("llama-3-8b", 8192),
    # DeepSeek
    ("deepseek-v3", 64000),
    ("deepseek-r1", 64000),
    ("deepseek-chat", 64000),
    # Qwen
    ("qwen2.5-72b", 128000),
    ("qwen2.5-32b", 128000),
    ("qwen2.5-14b", 128000),
    ("qwen2.5-7b", 128000),
    # Mistral
    ("mistral-large", 128000),
    ("mistral-medium", 32000),
    ("mistral-small", 32000),
    ("mixtral", 32000),
    ("pixtral", 128000),
    # NVIDIA Nemotron
    ("nemotron-4", 128000),
    ("nemotron-3", 128000),
    # Cohere
    ("command-r-plus", 128000),
    ("command-r", 128000),
    ("command-a", 256000),
    # Phi
    ("phi-4", 16000),
    ("phi-3", 128000),
]


def get_context_window(model_id: str, provider: str = "") -> int:
    """Returns the approximate context window for a model ID."""
    mid = model_id.lower()
    for pattern, ctx in _CONTEXT_WINDOW_RULES:
        if pattern.lower() in mid:
            return ctx
    # Provider fallback
    if provider in ("gemini",):
        return 1000000
    if provider in ("github", "openrouter", "nvidia", "mistral", "ollama"):
        return 128000
    if provider in ("groq", "sambanova", "cerebras"):
        return 8192
    return 128000  # Default generous fallback


def get_max_images(model_id: str, provider: str) -> int:
    """Returns max images per request, or -1 for unlimited/unknown."""
    meta = PROVIDER_METADATA.get(provider, {})
    limit = meta.get("max_images_per_request")
    if limit is not None:
        return limit
    # Heuristic fallback
    if "groq" in provider:
        return 5
    if "gemini" in provider:
        return 1000
    return -1


def supports_tools(model_id: str, provider: str) -> bool:
    """Heuristic: does this model support function calling/tools?"""
    meta = PROVIDER_METADATA.get(provider, {})
    base = meta.get("supports_tools", False)
    if not base:
        return False
    # Some models within providers explicitly don't support tools
    mid = model_id.lower()
    if provider == "ollama":
        # Most local models don't, some new do
        if any(x in mid for x in ["llava", "moondream", "nomic", "phi-2"]):
            return False
    if "embedding" in mid or "rerank" in mid or "tts" in mid:
        return False
    return True


def supports_streaming(model_id: str, provider: str) -> bool:
    """Returns whether this provider/model supports streaming."""
    meta = PROVIDER_METADATA.get(provider, {})
    return meta.get("supports_streaming", False)


def supports_reasoning_stream(model_id: str, provider: str) -> bool:
    """Returns whether this model emits separate reasoning/thinking tokens in stream."""
    mid = model_id.lower()
    # Known reasoning streamers
    if "deepseek-r1" in mid or "o1" in mid or "o3" in mid or "qwq" in mid:
        return True
    meta = PROVIDER_METADATA.get(provider, {})
    return meta.get("supports_reasoning_stream", False)


def get_input_modalities(model_id: str, provider: str, capabilities: list) -> list:
    """Returns supported input modalities based on metadata and capabilities."""
    meta = PROVIDER_METADATA.get(provider, {})
    base = list(meta.get("input_modalities", ["text"]))
    caps = set(capabilities)
    if VISION in caps and "image" not in base:
        base.append("image")
    if AUDIO in caps and "audio" not in base:
        base.append("audio")
    if FILE in caps and "pdf" not in base:
        base.append("pdf")
        base.append("video")
    return list(set(base))


def get_output_modalities(model_id: str, provider: str, capabilities: list) -> list:
    """Returns supported output modalities."""
    meta = PROVIDER_METADATA.get(provider, {})
    base = list(meta.get("output_modalities", ["text"]))
    caps = set(capabilities)
    if IMAGE_GEN in caps and "image" not in base:
        base.append("image")
    if VIDEO_GEN in caps and "video" not in base:
        base.append("video")
    if TTS in caps and "audio" not in base:
        base.append("audio")
    return list(set(base))


def get_pricing_tier(model_id: str, provider: str, capabilities: list) -> str:
    """Returns 'free', 'paid', or 'mixed' for a model.

    The FREE capability flag (set by _add_free_flag in model_fetcher.py) is the
    source of truth. It already applies provider-specific and model-specific rules
    (e.g., OpenRouter :free suffix, Mistral small/medium/pixtral, Gemini flash/pro).
    """
    caps = set(capabilities)
    if FREE in caps:
        return "free"
    return "paid"


def build_model_metadata(model_id: str, provider: str, capabilities: list) -> dict:
    """
    Builds the complete metadata dict that clients (IDEs, apps) need
    to make intelligent routing and UI decisions.
    """
    return {
        "context_window": get_context_window(model_id, provider),
        "max_images_per_request": get_max_images(model_id, provider),
        "supports_tools": supports_tools(model_id, provider),
        "supports_streaming": supports_streaming(model_id, provider),
        "supports_reasoning_stream": supports_reasoning_stream(model_id, provider),
        "input_modalities": get_input_modalities(model_id, provider, capabilities),
        "output_modalities": get_output_modalities(model_id, provider, capabilities),
        "pricing_tier": get_pricing_tier(model_id, provider, capabilities),
        "provider_limits": PROVIDER_METADATA.get(provider, {}),
    }


# --- Dynamic Model Registry ---
MODELS_REGISTRY = []

# --- Proxy Security ---
PROXY_API_KEY_ENV = "PROXY_API_KEY"
