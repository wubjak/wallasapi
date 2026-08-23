"""Offline tests for the web search engine (no network, no API keys)."""
from unittest.mock import MagicMock

import pytest

from wallasAPI import search_engine as se_mod
from wallasAPI.search_engine import WebSearchEngine


class FakeDDGS:
    """Imita el context manager de ddgs/duckduckgo_search."""

    results = [{"title": "T1", "href": "https://ex.com", "body": "<b>snippet</b>"}]
    fail = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def text(self, query, max_results=10):
        if self.fail:
            raise RuntimeError("blocked")
        return iter(self.results[:max_results])


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setattr(se_mod, "HAS_DDGS", True)
    monkeypatch.setattr(se_mod, "DDGS", FakeDDGS)
    return WebSearchEngine()


def test_duckduckgo_results_normalized(engine):
    r = engine.search("python", max_results=5)
    assert r["backend_used"] == "duckduckgo"
    assert r["fallback"] is False
    assert r["count"] == 1
    item = r["results"][0]
    assert item == {"title": "T1", "url": "https://ex.com", "snippet": "snippet", "source": "duckduckgo"}


def test_cache_prevents_second_backend_call(engine, monkeypatch):
    calls = {"n": 0}
    orig_text = FakeDDGS.text

    def counting_text(self, query, max_results=10):
        calls["n"] += 1
        return orig_text(self, query, max_results)

    monkeypatch.setattr(FakeDDGS, "text", counting_text)
    engine.search("same query")
    engine.search("same query")
    assert calls["n"] == 1


def test_fallback_to_google_cse_when_ddg_fails(engine, monkeypatch):
    monkeypatch.setattr(FakeDDGS, "fail", True)
    monkeypatch.setenv("GOOGLE_CSE_KEY", "k")
    monkeypatch.setenv("GOOGLE_CSE_ID", "cx")
    monkeypatch.setattr(se_mod, "HAS_REQUESTS", True)

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"items": [{"title": "G", "link": "https://g.com", "snippet": "gs"}]}
    fake_resp.raise_for_status.return_value = None
    monkeypatch.setattr(se_mod.requests, "get", lambda *a, **k: fake_resp)

    r = engine.search("python")
    assert r["backend_used"] == "google_cse"
    assert r["fallback"] is True
    assert r["results"][0]["source"] == "google_cse"


def test_all_backends_fail_returns_error_dict(engine, monkeypatch):
    monkeypatch.setattr(FakeDDGS, "fail", True)
    monkeypatch.delenv("GOOGLE_CSE_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    r = engine.search("python")
    assert r["count"] == 0
    assert r["backend_used"] == "none"
    assert "error" in r


def test_search_and_summarize_builds_context(engine):
    ctx = engine.search_and_summarize("python", router=None)
    assert "CONTEXTO DE BÚSQUEDA WEB" in ctx
    assert "T1" in ctx
    assert "https://ex.com" in ctx
