"""
WallasAPI Search Engine — Dos backends de búsqueda web para el ecosistema Gravedad.

Backend 1: DuckDuckGo (gratis, sin API key, vía duckduckgo-search)
Backend 2: Google Custom Search / SerpAPI (requiere API key, más completo)
Backend 3: Gemini Search Grounding (cuando está disponible)
"""
import os
import time
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .logger import log


def _clean_html(text: str) -> str:
    """Strip basic HTML tags."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class WebSearchEngine:
    """
    Motor de búsqueda web dual para WallasAPI/Gravedad.
    Intenta múltiples backends y devuelve resultados unificados.
    """

    def __init__(self):
        self._last_backend: Optional[str] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 120  # segundos

    # ------------------------------------------------------------------
    # Backend 1: DuckDuckGo (gratis, sin API key)
    # ------------------------------------------------------------------
    def _search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search using DuckDuckGo (no API key required)."""
        if not HAS_DDGS:
            raise RuntimeError("duckduckgo-search no instalado. Instala: pip install duckduckgo-search")

        results = []
        # 1. Intentar con el método estándar text()
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": _clean_html(r.get("body", "")),
                        "source": "duckduckgo",
                    })
        except Exception as e:
            log.warning(f"[SEARCH] DuckDuckGo text() falló para '{query}': {e}. Intentando fallback a html...")

        # 2. Fallback resiliente a _text_html() si text() dio vacío o falló
        if not results:
            try:
                log.info(f"[SEARCH] DuckDuckGo text() no devolvió resultados para '{query}'. Probando fallback _text_html()...")
                with DDGS() as ddgs:
                    for r in ddgs._text_html(query, max_results=max_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": _clean_html(r.get("body", "")),
                            "source": "duckduckgo_html",
                        })
            except Exception as e:
                log.error(f"[SEARCH] Fallback DuckDuckGo _text_html() también falló para '{query}': {e}")
                if not results:
                    raise

        return results

    # ------------------------------------------------------------------
    # Backend 2: Google Custom Search (requiere GOOGLE_CSE_KEY + GOOGLE_CSE_ID)
    # ------------------------------------------------------------------
    def _search_google_cse(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search using Google Custom Search Engine (requires API key)."""
        api_key = os.getenv("GOOGLE_CSE_KEY")
        cse_id = os.getenv("GOOGLE_CSE_ID")
        if not api_key or not cse_id:
            raise RuntimeError("GOOGLE_CSE_KEY y GOOGLE_CSE_ID no configurados")

        if not HAS_REQUESTS:
            raise RuntimeError("requests no instalado")

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(max_results, 10),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": _clean_html(item.get("snippet", "")),
                "source": "google_cse",
            })
        return results

    # ------------------------------------------------------------------
    # Backend 3: SerpAPI (requiere SERPAPI_KEY)
    # ------------------------------------------------------------------
    def _search_serpapi(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search using SerpAPI (requires API key)."""
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            raise RuntimeError("SERPAPI_KEY no configurado")
        if not HAS_REQUESTS:
            raise RuntimeError("requests no instalado")

        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": min(max_results, 10),
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": _clean_html(item.get("snippet", "")),
                "source": "serpapi",
            })
        return results

    # ------------------------------------------------------------------
    # Motor principal con fallback
    # ------------------------------------------------------------------
    def search(self, query: str, max_results: int = 10, preferred_backend: str = "auto") -> Dict[str, Any]:
        """
        Busca en la web usando múltiples backends con fallback automático.

        Args:
            query: Término de búsqueda
            max_results: Máximo de resultados por backend
            preferred_backend: "auto", "duckduckgo", "google_cse", "serpapi"

        Returns:
            Dict con {"results": [...], "backend_used": str, "fallback": bool, "query": str}
        """
        cache_key = f"{query}:{max_results}:{preferred_backend}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached.get("_ts", 0)) < self._cache_ttl:
            return cached["data"]

        backends = []
        if preferred_backend == "auto":
            backends = ["duckduckgo", "google_cse", "serpapi"]
        else:
            backends = [preferred_backend]

        for backend in backends:
            try:
                if backend == "duckduckgo":
                    results = self._search_duckduckgo(query, max_results)
                elif backend == "google_cse":
                    results = self._search_google_cse(query, max_results)
                elif backend == "serpapi":
                    results = self._search_serpapi(query, max_results)
                else:
                    continue

                if results:
                    self._last_backend = backend
                    result = {
                        "query": query,
                        "results": results,
                        "backend_used": backend,
                        "fallback": backend != backends[0],
                        "count": len(results),
                    }
                    self._cache[cache_key] = {"data": result, "_ts": time.time()}
                    log.info(f"[SEARCH] {backend}: {len(results)} resultados para '{query}'")
                    return result

            except Exception as e:
                log.warning(f"[SEARCH] Backend {backend} falló para '{query}': {e}")
                continue

        # Todos fallaron
        return {
            "query": query,
            "results": [],
            "backend_used": "none",
            "fallback": False,
            "count": 0,
            "error": "Todos los backends de búsqueda fallaron",
        }

    def search_and_summarize(self, query: str, router: Any, max_results: int = 8) -> str:
        """
        Busca en la web y usa un modelo de IA para resumir los resultados.
        Devuelve un string listo para inyectar como contexto en prompts.
        """
        search_data = self.search(query, max_results=max_results)
        if not search_data["results"]:
            return "[No se encontraron resultados de búsqueda web]"

        # Formatear resultados como contexto
        lines = ["=== CONTEXTO DE BÚSQUEDA WEB ===", f"Query: {query}", ""]
        for i, r in enumerate(search_data["results"][:5], 1):
            lines.append(f"[{i}] {r['title']}\n{r['snippet']}\nFuente: {r['url']}\n")
        lines.append("=== FIN CONTEXTO ===")
        return "\n".join(lines)


# Singleton
_search_engine: Optional[WebSearchEngine] = None

def get_search_engine() -> WebSearchEngine:
    global _search_engine
    if _search_engine is None:
        _search_engine = WebSearchEngine()
    return _search_engine
