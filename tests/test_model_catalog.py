"""Offline contract tests for normalized catalog and virtual routing."""
from wallasAPI.model_catalog import (
    AGENTIC, AUDIO, CODE, LONG_CONTEXT, REASONING, TOOLS, VISION,
    detect_auto_profile, enrich_legacy_entry, normalize_model, rank_candidates,
)
from wallasAPI import model_fetcher


def test_glm_52_nvidia_is_agentic_coding_reasoning_and_text_only():
    record = normalize_model("nvidia", "z-ai/glm-5.2")
    assert {AGENTIC, CODE, REASONING, TOOLS, LONG_CONTEXT} <= record.capabilities
    assert VISION not in record.capabilities
    assert AUDIO not in record.capabilities
    assert record.context_window == 1_000_000
    assert record.cost_class == "free_endpoint"


def test_model_specific_override_does_not_leak_provider_capabilities():
    command = normalize_model("cohere", "command-a-plus-05-2026")
    plain = normalize_model("cohere", "command-r7b")
    assert VISION in command.capabilities
    assert VISION not in plain.capabilities


def test_retired_and_paid_models_are_excluded_from_automatic_profiles():
    retired = enrich_legacy_entry({"provider": "gemini", "id": "gemini-2.0-flash", "capabilities": ["text"]})
    paid = enrich_legacy_entry({"provider": "cohere", "id": "command-a-plus-05-2026", "capabilities": ["text"]})
    glm = enrich_legacy_entry({"provider": "nvidia", "id": "z-ai/glm-5.2", "capabilities": ["text"]})
    accepted, rejected = rank_candidates([retired, paid, glm], profile="agentico", tools_requested=True)
    assert [(m["provider"], m["id"]) for m in accepted] == [("nvidia", "z-ai/glm-5.2")]
    assert {r["reason"] for r in rejected} >= {"lifecycle:retired", "cost:trial"}


def test_auto_signals_have_deterministic_priority():
    assert detect_auto_profile("describe this", images=True)[0] == "vision"
    assert detect_auto_profile("fix it", tools=True)[0] == "agentico"
    assert detect_auto_profile("```python\nprint(1)\n```")[0] == "codigo"
    assert detect_auto_profile("short", required_context=200_000)[0] == "contexto-largo"


def test_provider_snapshot_survives_a_partial_refresh_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(model_fetcher, "registry_cache_path", lambda: tmp_path / "models_registry.json")
    model_fetcher._save_provider_snapshot("nvidia", [{"provider": "nvidia", "id": "z-ai/glm-5.2", "capabilities": ["text"]}])
    restored = model_fetcher._load_provider_snapshot("nvidia")
    assert restored[0]["id"] == "z-ai/glm-5.2"
    assert restored[0]["stale"] is True
