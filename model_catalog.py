"""Normalized model records and virtual-profile routing for WallasAPI."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Optional, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field

TEXT, VISION, AUDIO, FILE = "text", "vision", "audio", "file"
REASONING, CODE, MOE, FREE = "reasoning", "code", "moe", "free"
AGENTIC, TOOLS, PARALLEL_TOOLS = "agentic", "tools", "parallel_tools"
STRUCTURED_OUTPUT, LONG_CONTEXT, STREAMING = "structured_output", "long_context", "streaming"
VIRTUAL_ALIASES = {"fast": "rapido", "reasoning": "razonamiento", "vista": "vision", "equilibrado": "standard"}
VIRTUAL_PROFILES = {
    "rapido": ({TEXT}, {STREAMING: 20}),
    "standard": ({TEXT}, {TOOLS: 10, STRUCTURED_OUTPUT: 10, STREAMING: 10}),
    "razonamiento": ({TEXT, REASONING}, {REASONING: 30, LONG_CONTEXT: 10, TOOLS: 10}),
    "agentico": ({TEXT, TOOLS}, {AGENTIC: 20, STRUCTURED_OUTPUT: 15, PARALLEL_TOOLS: 10, REASONING: 10, LONG_CONTEXT: 5}),
    "codigo": ({TEXT, CODE}, {CODE: 30, REASONING: 10, TOOLS: 10, LONG_CONTEXT: 10}),
    "vision": ({TEXT, VISION}, {VISION: 25, REASONING: 15, STRUCTURED_OUTPUT: 10}),
    "multimodal": ({TEXT}, {VISION: 10, AUDIO: 10, FILE: 10, REASONING: 10}),
    "contexto-largo": ({TEXT, LONG_CONTEXT}, {LONG_CONTEXT: 30, REASONING: 10, TOOLS: 10}),
}


class ModelRecord(BaseModel):
    model_config = ConfigDict(extra="allow")
    provider: str
    id: str
    author: str = "unknown"
    canonical_id: Optional[str] = None
    route_id: Optional[str] = None
    model_type: Literal["chat", "embedding", "rerank", "tts", "asr", "ocr", "safety", "detector", "image_generation", "video_generation", "other"] = "chat"
    capabilities: Set[str] = Field(default_factory=set)
    input_modalities: Set[str] = Field(default_factory=lambda: {TEXT})
    output_modalities: Set[str] = Field(default_factory=lambda: {TEXT})
    context_window: int = 0
    max_output_tokens: Optional[int] = None
    supported_parameters: Set[str] = Field(default_factory=set)
    family: Optional[str] = None
    version: Optional[str] = None
    parameter_count: Optional[str] = None
    is_moe: bool = False
    cost_class: Literal["local", "free_endpoint", "free_tier", "trial", "paid", "unknown"] = "unknown"
    lifecycle: Literal["active", "preview", "deprecated", "retired", "unknown"] = "unknown"
    quality_score: int = 50
    source: str = "heuristic"
    source_url: Optional[str] = None
    verified_at: Optional[str] = None
    confidence: str = "heuristic"
    availability: Literal["available", "unavailable", "unknown"] = "unknown"
    stale: bool = False
    last_latency_ms: Optional[int] = None
    recent_success: Optional[bool] = None
    rate_limited: bool = False
    cooldown_until: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        self.canonical_id = self.canonical_id or f"{self.provider}:{self.id}"
        self.route_id = self.route_id or f"{self.provider}::{self.id}"
        if self.model_type == "chat": self.capabilities.add(TEXT)
        if self.context_window >= 262144: self.capabilities.add(LONG_CONTEXT)
        if self.cost_class in {"local", "free_endpoint", "free_tier"}: self.capabilities.add(FREE)
        if MOE in self.capabilities: self.is_moe = True

    def metadata(self) -> Dict[str, Any]:
        return {"context_window": self.context_window or 128000, "max_output_tokens": self.max_output_tokens, "supported_parameters": sorted(self.supported_parameters), "supports_tools": TOOLS in self.capabilities, "supports_streaming": STREAMING in self.capabilities, "supports_reasoning_stream": REASONING in self.capabilities, "input_modalities": sorted(self.input_modalities), "output_modalities": sorted(self.output_modalities), "pricing_tier": "free" if FREE in self.capabilities else "paid", "model_type": self.model_type, "capability_tags": sorted(self.capabilities), "virtual_profiles": virtual_profiles_for(self), "cost": self.cost_class, "lifecycle": self.lifecycle, "source": self.source, "source_url": self.source_url, "verified_at": self.verified_at, "confidence": self.confidence, "canonical_id": self.canonical_id, "route_id": self.route_id, "freshness": "stale" if self.stale else "fresh", "availability": self.availability, "last_latency_ms": self.last_latency_ms}


class RoutingRequest(BaseModel):
    model: str = "auto"
    prompt: str = ""
    required_modalities: Set[str] = Field(default_factory=lambda: {TEXT})
    tools_requested: bool = False
    structured_output_requested: bool = False
    required_context: int = 0
    max_output_tokens: int = 4096
    preferred_provider: Optional[str] = None
    cost_mode: Literal["free_only", "allow_paid"] = "free_only"


class RoutingPlan(BaseModel):
    requested_profile: str
    profile: str
    signals: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    router_mode: Literal["legacy", "shadow", "v2"] = "v2"
    candidates: list[Dict[str, Any]] = Field(default_factory=list)
    rejected: list[Dict[str, Any]] = Field(default_factory=list)
    shadow_candidates: list[Dict[str, Any]] = Field(default_factory=list)
    legacy_candidates: list[Dict[str, Any]] = Field(default_factory=list)


class RouterResult(BaseModel):
    content: str = ""
    reasoning: Optional[str] = None
    tool_calls: list[Dict[str, Any]] = Field(default_factory=list)
    finish_reason: str = "stop"
    usage: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    model: Optional[str] = None


def _overrides() -> Dict[str, Any]:
    try: return json.loads(Path(__file__).with_name("model_overrides.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {"models": [], "lifecycle_overrides": []}
OVERRIDES = _overrides()

def cache_dir() -> Path:
    if os.getenv("WALLAS_CACHE_DIR"): return Path(os.environ["WALLAS_CACHE_DIR"])
    if sys.platform.startswith("win"): return Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "WallasAPI" / "cache"
    return Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "wallasapi"


def registry_cache_path() -> Path:
    """Runtime registry snapshot location, deliberately outside the repository."""
    return cache_dir() / "models_registry.json"

def normalize_model(provider: str, model_id: str, raw: Optional[Dict[str, Any]] = None) -> ModelRecord:
    raw, mid = raw or {}, model_id.lower(); caps: Set[str] = {TEXT}; inputs = {TEXT}; outputs = {TEXT}
    if any(x in mid for x in ("embedding", "embed-")): kind, caps = "embedding", set()
    elif "rerank" in mid: kind, caps = "rerank", set()
    elif "tts" in mid: kind, caps = "tts", set()
    elif any(x in mid for x in ("whisper", "transcribe", "asr")): kind, caps = "asr", set()
    elif "ocr" in mid: kind, caps = "ocr", set()
    elif any(x in mid for x in ("guard", "safety", "moderation")): kind, caps = "safety", set()
    elif any(x in mid for x in ("detector", "detection")): kind, caps = "detector", set()
    elif any(x in mid for x in ("flux", "imagen", "dall-e", "stable-diffusion")): kind, caps = "image_generation", set()
    elif any(x in mid for x in ("veo", "sora", "runway")): kind, caps = "video_generation", set()
    else: kind = "chat"
    if any(x in mid for x in ("vision", "-vl", "llava", "pixtral", "cosmos", "minimax-m3")): caps.add(VISION); inputs.add("image")
    if any(x in mid for x in ("reasoning", "thinking", "-r1", "qwq", "glm-5", "deepseek-v4", "nemotron-3")): caps.add(REASONING)
    if any(x in mid for x in ("coder", "codestral", "devstral", "glm-5", "deepseek-v4", "gpt-oss")): caps.add(CODE)
    if any(x in mid for x in ("glm-5", "agent", "devstral", "gpt-oss", "nemotron-3-ultra", "kimi-k2", "minimax-m3")): caps.add(AGENTIC)
    if any(x in mid for x in ("mixtral", "moe", "nemotron", "glm-5", "minimax", "deepseek-v4")): caps.add(MOE)
    pcaps = raw.get("capabilities", {}) if isinstance(raw.get("capabilities"), dict) else {}; parameters = set(raw.get("supported_parameters", []) or [])
    if pcaps.get("function_calling") or pcaps.get("tools") or "tools" in parameters: caps.add(TOOLS)
    if pcaps.get("parallel_tool_calls") or "parallel_tool_calls" in parameters: caps.add(PARALLEL_TOOLS)
    if pcaps.get("structured_outputs") or "response_format" in parameters: caps.add(STRUCTURED_OUTPUT)
    if kind == "chat" or pcaps.get("streaming"): caps.add(STREAMING)
    cost = "local" if provider == "ollama" else "free_tier" if provider in {"groq", "sambanova", "github", "nvidia", "cerebras"} else "free_endpoint" if provider == "pollinations" or (provider == "openrouter" and ":free" in mid) else "paid" if provider in {"openai", "mistral"} else "trial" if provider == "cohere" else "unknown"
    data: Dict[str, Any] = {"provider": provider, "id": model_id, "author": model_id.split('/', 1)[0] if '/' in model_id else provider, "model_type": kind, "capabilities": caps, "input_modalities": inputs, "output_modalities": outputs, "context_window": int(raw.get("context_length") or raw.get("context_window") or raw.get("inputTokenLimit") or raw.get("limits", {}).get("max_context_length") or 0), "max_output_tokens": raw.get("max_output_tokens") or raw.get("outputTokenLimit"), "supported_parameters": parameters, "cost_class": cost, "lifecycle": "preview" if raw.get("preview") else "active", "source": "provider" if raw else "heuristic", "availability": "available", "stale": bool(raw.get("stale", False)), "last_latency_ms": raw.get("last_latency_ms"), "recent_success": raw.get("alive")}
    for item in OVERRIDES.get("models", []):
        if item.get("provider", "").lower() == provider.lower() and item.get("id", "").lower() == mid:
            data.update({k:v for k,v in item.items() if k not in {"provider", "id"}})
            data["source"] = "official_override"
            data["verified_at"] = OVERRIDES.get("verified_at")
    for item in OVERRIDES.get("lifecycle_overrides", []):
        if item.get("provider", "").lower() == provider.lower() and item.get("pattern", "").lower() in mid: data["lifecycle"] = item["lifecycle"]
    return ModelRecord.model_validate(data)

def enrich_legacy_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(entry.get("source_metadata") or {}); raw.update({k: entry[k] for k in ("stale", "last_latency_ms", "alive") if k in entry})
    record = normalize_model(entry.get("provider", "unknown"), entry.get("id", ""), raw); result = dict(entry)
    result["capabilities"], result["metadata"], result["catalog"] = sorted(record.capabilities), record.metadata(), record.model_dump(mode="json")
    return result

def virtual_profiles_for(record: ModelRecord) -> list[str]:
    return [name for name, (required, _) in VIRTUAL_PROFILES.items() if record.model_type == "chat" and record.lifecycle == "active" and required <= record.capabilities]

def detect_auto_profile(prompt: str = "", *, images=False, audio=False, files=False, tools=False, reasoning=False, required_context=0) -> Tuple[str, list[str], float]:
    if images and not(audio or files): return "vision", ["image_input"], 1.0
    if images or audio or files: return "multimodal", ["non_text_input"], 1.0
    if tools: return "agentico", ["tools_requested"], 1.0
    if required_context > 131072: return "contexto-largo", ["context_over_128k"], 1.0
    low = prompt.lower()
    if any(x in low for x in ("traceback", "stack trace", "```", "git diff", "refactor", "python", "typescript")): return "codigo", ["code_signal"], .9
    if reasoning or any(x in low for x in ("razona", "demuestra", "paso a paso")): return "razonamiento", ["reasoning_signal"], .85
    if len(prompt) < 280 and any(x in low for x in ("resume", "traduce", "clasifica", "extrae")): return "rapido", ["simple_short_request"], .75
    return "standard", ["ambiguous_text"], .5

def rank_candidates(entries: Iterable[Dict[str, Any]], *, profile: str, required_context=0, required_modalities: Optional[Set[str]]=None, tools_requested=False, cost_mode="free_only", allow_paid=False, preferred_provider=None):
    profile = VIRTUAL_ALIASES.get(profile, profile); required, weights = VIRTUAL_PROFILES.get(profile, VIRTUAL_PROFILES["standard"]); required = set(required) | ({TOOLS} if tools_requested else set()); modalities = required_modalities or {TEXT}; accepted=[]; rejected=[]
    for entry in entries:
        record = ModelRecord.model_validate(entry["catalog"]) if entry.get("catalog") else normalize_model(entry.get("provider", ""), entry.get("id", ""))
        if record.model_type != "chat": reason="not_chat"
        elif record.lifecycle != "active": reason=f"lifecycle:{record.lifecycle}"
        elif not required <= record.capabilities: reason="missing:"+",".join(sorted(required-record.capabilities))
        elif not modalities <= (record.input_modalities|{TEXT}): reason="missing_modalities"
        elif required_context and record.context_window and record.context_window < required_context: reason="insufficient_context"
        elif cost_mode == "free_only" and record.cost_class not in {"local", "free_endpoint", "free_tier"}: reason=f"cost:{record.cost_class}"
        elif cost_mode != "free_only" and record.cost_class == "unknown": reason="cost:unknown"
        elif cost_mode != "free_only" and record.cost_class in {"paid", "trial"} and not allow_paid: reason="paid_not_enabled"
        else: reason=None
        if reason: rejected.append({"provider":record.provider,"id":record.id,"reason":reason}); continue
        score=sum(v for cap,v in weights.items() if cap in record.capabilities)+record.quality_score*.15+(1 if preferred_provider==record.provider else 0)
        accepted.append((score,record.route_id,entry))
    accepted.sort(key=lambda v:(-v[0],v[1])); return [v[2] for v in accepted],rejected
