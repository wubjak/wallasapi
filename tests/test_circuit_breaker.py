"""Offline tests for the router circuit breaker (no network, no API keys)."""
import pytest

from wallasAPI import router as router_mod
from wallasAPI.router import AIRouter


@pytest.fixture
def router():
    return AIRouter()


def fake_clock(start=1000.0):
    state = {"t": start}
    return lambda: state["t"], state


def test_fresh_provider_is_available(router):
    assert router._is_available("gemini/gemini-2.0-flash") is True


def test_failure_opens_circuit_with_300s_cooldown(router, monkeypatch):
    clock, t = fake_clock()
    monkeypatch.setattr(router_mod.time, "time", clock)

    router._mark_failure("gemini/gemini-2.0-flash", "timeout")
    assert router._is_available("gemini/gemini-2.0-flash") is False

    t["t"] += 299
    assert router._is_available("gemini/gemini-2.0-flash") is False
    t["t"] += 2
    assert router._is_available("gemini/gemini-2.0-flash") is True


def test_cooldown_escalates_with_consecutive_failures(router, monkeypatch):
    clock, t = fake_clock()
    monkeypatch.setattr(router_mod.time, "time", clock)

    key = "groq/llama-3.3-70b-versatile"
    router._mark_failure(key, "500")
    t["t"] += 301
    router._mark_failure(key, "500")  # fail_count=2 -> 600s
    assert router._is_available(key) is False
    t["t"] += 500
    assert router._is_available(key) is False
    t["t"] += 101
    assert router._is_available(key) is True


def test_success_resets_circuit_and_tracks_latency(router, monkeypatch):
    clock, t = fake_clock()
    monkeypatch.setattr(router_mod.time, "time", clock)

    key = "openrouter/model-x"
    router._mark_failure(key, "timeout")
    router._mark_success(key, latency_ms=100.0, thread_id="th1")

    assert router._is_available(key) is True
    stats = {c["key"]: c for c in router.get_circuit_stats()["circuits"]}
    assert stats[key]["fail_count"] == 0
    assert stats[key]["success_count"] == 1
    assert stats[key]["avg_latency_ms"] == 100.0
    assert router._last_success_cache["th1"][0] == "openrouter"


def test_latency_is_exponential_moving_average(router):
    key = "p/m"
    router._mark_success(key, latency_ms=100.0)
    router._mark_success(key, latency_ms=200.0)
    state = router._circuit[key]
    assert abs(state["avg_latency_ms"] - 130.0) < 0.01
