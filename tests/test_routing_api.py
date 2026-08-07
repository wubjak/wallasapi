"""Offline API contracts for routing headers, cost policy and tool calls."""
import json

from fastapi.testclient import TestClient

from wallasAPI import api_server


PLANNED = [{
    "provider": "nvidia",
    "id": "z-ai/glm-5.2",
    "catalog": {"route_id": "nvidia::z-ai/glm-5.2"},
}]


def _install_plan(monkeypatch):
    def plan(**_kwargs):
        api_server.router._last_routing_plan = {
            "profile": "agentico", "signals": ["tools_requested"],
            "candidates": [{"provider": "nvidia", "id": "z-ai/glm-5.2"}],
            "rejected": [],
        }
        return PLANNED
    monkeypatch.setattr(api_server.router, "_get_ordered_model_list", plan)


def test_non_streaming_preserves_tool_calls_and_routing_headers(monkeypatch):
    _install_plan(monkeypatch)
    monkeypatch.setattr(
        api_server.router,
        "get_completion",
        lambda **_kwargs: ({"content": "", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "search", "arguments": "{\"q\":\"Lima\"}"}}]}, "nvidia", "z-ai/glm-5.2"),
    )
    response = TestClient(api_server.app).post("/v1/chat/completions", json={
        "model": "agentico",
        "messages": [{"role": "user", "content": "busca Lima"}],
        "tools": [{"type": "function", "function": {"name": "search", "parameters": {"type": "object"}}}],
    })
    assert response.status_code == 200
    assert response.headers["x-wallas-provider"] == "nvidia"
    assert response.headers["x-wallas-route-id"] == "nvidia::z-ai/glm-5.2"
    assert response.json()["choices"][0]["finish_reason"] == "tool_calls"
    assert response.json()["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "search"


def test_paid_mode_requires_operator_and_request_authorization(monkeypatch):
    monkeypatch.delenv("WALLAS_ALLOW_PAID", raising=False)
    response = TestClient(api_server.app).post(
        "/v1/chat/completions",
        headers={"X-Wallas-Cost-Mode": "allow_paid"},
        json={"model": "standard", "messages": [{"role": "user", "content": "hola"}]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "paid_mode_not_enabled"


def test_streaming_emits_tool_call_deltas_and_headers(monkeypatch):
    _install_plan(monkeypatch)

    def stream(**_kwargs):
        yield {"type": "metadata", "provider": "nvidia", "model": "z-ai/glm-5.2"}
        yield {"type": "tool_calls", "chunk": [{"index": 0, "id": "call_1", "type": "function", "function": {"name": "search", "arguments": "{}"}}]}

    monkeypatch.setattr(api_server.router, "stream_completion", stream)
    response = TestClient(api_server.app).post("/v1/chat/completions", json={
        "model": "agentico", "stream": True,
        "messages": [{"role": "user", "content": "busca"}],
        "tools": [{"type": "function", "function": {"name": "search", "parameters": {"type": "object"}}}],
    })
    assert response.status_code == 200
    assert response.headers["x-wallas-profile"] == "agentico"
    assert '"tool_calls"' in response.text
    assert '"finish_reason": "tool_calls"' in response.text
