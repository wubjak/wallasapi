"""
WallasAPI — Camofox Browser Integration
========================================

Wraps camofox-browser REST API for AI agent browsing, scraping, and interaction.

Camofox runs as a separate server (default: http://localhost:9377).
Install: npm install -g camofox-browser
Start:   camofox-browser server

Provides:
  - Open URL and get accessibility snapshot (~90% smaller than raw HTML)
  - Click, type, scroll, navigate via element refs (e1, e2, e3...)
  - Search macros (@google_search, @youtube_search, etc.)
  - Screenshots as base64 PNG
  - YouTube transcripts
  - Session isolation per user
"""

import os
import base64
from typing import Optional, Dict, Any, List
import httpx


CAMOFOX_BASE_URL = os.getenv("CAMOFOX_URL", "http://localhost:9377")


class CamofoxClient:
    """Lightweight async client for camofox-browser REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = (base_url or CAMOFOX_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def health(self) -> Dict[str, Any]:
        """Check if camofox server is running."""
        try:
            client = await self._get_client()
            r = await client.get(f"{self.base_url}/health")
            return {"ok": r.status_code == 200, "status": r.status_code, "data": r.json() if r.status_code == 200 else None}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def open_tab(
        self,
        url: str,
        user_id: str = "wallasapi_default",
        session_key: Optional[str] = None,
        wait_for_load: bool = True,
    ) -> Dict[str, Any]:
        """Create a new browser tab and navigate to URL."""
        client = await self._get_client()
        payload = {
            "userId": user_id,
            "url": url,
            "waitForLoad": wait_for_load,
        }
        if session_key:
            payload["sessionKey"] = session_key

        r = await client.post(f"{self.base_url}/tabs", json=payload)
        r.raise_for_status()
        return r.json()

    async def snapshot(
        self,
        tab_id: str,
        user_id: str = "wallasapi_default",
        include_screenshot: bool = False,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get accessibility snapshot with element refs."""
        client = await self._get_client()
        params: Dict[str, Any] = {"userId": user_id}
        if include_screenshot:
            params["includeScreenshot"] = "true"
        if offset is not None:
            params["offset"] = offset

        r = await client.get(f"{self.base_url}/tabs/{tab_id}/snapshot", params=params)
        r.raise_for_status()
        return r.json()

    async def click(
        self,
        tab_id: str,
        ref: str,
        user_id: str = "wallasapi_default",
    ) -> Dict[str, Any]:
        """Click an element by its ref (e.g. e1, e2)."""
        client = await self._get_client()
        r = await client.post(
            f"{self.base_url}/tabs/{tab_id}/click",
            json={"userId": user_id, "ref": ref},
        )
        r.raise_for_status()
        return r.json()

    async def type_text(
        self,
        tab_id: str,
        ref: str,
        text: str,
        user_id: str = "wallasapi_default",
        press_enter: bool = False,
    ) -> Dict[str, Any]:
        """Type text into an element ref."""
        client = await self._get_client()
        payload = {"userId": user_id, "ref": ref, "text": text}
        if press_enter:
            payload["pressEnter"] = True
        r = await client.post(f"{self.base_url}/tabs/{tab_id}/type", json=payload)
        r.raise_for_status()
        return r.json()

    async def navigate_macro(
        self,
        tab_id: str,
        macro: str,
        query: Optional[str] = None,
        user_id: str = "wallasapi_default",
    ) -> Dict[str, Any]:
        """Navigate using a search macro (@google_search, @youtube_search, etc.)."""
        client = await self._get_client()
        payload = {"userId": user_id, "macro": macro}
        if query:
            payload["query"] = query
        r = await client.post(f"{self.base_url}/tabs/{tab_id}/navigate", json=payload)
        r.raise_for_status()
        return r.json()

    async def scroll(self, tab_id: str, user_id: str = "wallasapi_default") -> Dict[str, Any]:
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/tabs/{tab_id}/scroll", json={"userId": user_id})
        r.raise_for_status()
        return r.json()

    async def press_key(self, tab_id: str, key: str, user_id: str = "wallasapi_default") -> Dict[str, Any]:
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/tabs/{tab_id}/press", json={"userId": user_id, "key": key})
        r.raise_for_status()
        return r.json()

    async def screenshot(self, tab_id: str, user_id: str = "wallasapi_default") -> Dict[str, Any]:
        """Get base64 PNG screenshot."""
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/tabs/{tab_id}/screenshot", params={"userId": user_id})
        r.raise_for_status()
        return r.json()

    async def links(self, tab_id: str, user_id: str = "wallasapi_default") -> Dict[str, Any]:
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/tabs/{tab_id}/links", params={"userId": user_id})
        r.raise_for_status()
        return r.json()

    async def close_tab(self, tab_id: str, user_id: str = "wallasapi_default") -> Dict[str, Any]:
        client = await self._get_client()
        r = await client.delete(f"{self.base_url}/tabs/{tab_id}", params={"userId": user_id})
        if r.status_code == 204:
            return {"status": "ok", "closed": True}
        r.raise_for_status()
        return r.json()

    async def youtube_transcript(
        self,
        url: str,
        languages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Extract YouTube transcript via camofox (uses yt-dlp if available)."""
        client = await self._get_client()
        payload = {"url": url}
        if languages:
            payload["languages"] = languages
        r = await client.post(f"{self.base_url}/youtube/transcript", json=payload)
        r.raise_for_status()
        return r.json()

    async def extract_structured(
        self,
        tab_id: str,
        schema: Dict[str, Any],
        user_id: str = "wallasapi_default",
    ) -> Dict[str, Any]:
        """Extract structured data from page using JSON Schema with x-ref mapping."""
        client = await self._get_client()
        r = await client.post(
            f"{self.base_url}/tabs/{tab_id}/extract",
            json={"userId": user_id, "schema": schema},
        )
        r.raise_for_status()
        return r.json()

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton for reuse across requests
_camofox_client: Optional[CamofoxClient] = None


def get_browser_client() -> CamofoxClient:
    global _camofox_client
    if _camofox_client is None:
        _camofox_client = CamofoxClient()
    return _camofox_client


async def browse_and_summarize(
    url: str,
    user_id: str = "wallasapi_default",
    max_snapshot_chars: int = 8000,
) -> Dict[str, Any]:
    """
    High-level helper: open URL, get snapshot, close tab.
    Returns snapshot text + metadata for LLM consumption.
    """
    client = get_browser_client()
    health = await client.health()
    if not health["ok"]:
        raise RuntimeError(f"Camofox no está disponible: {health.get('error', 'unknown')}")

    tab = await client.open_tab(url, user_id=user_id)
    tab_id = tab.get("tabId") or tab.get("id")
    if not tab_id:
        raise RuntimeError(f"Camofox no devolvió tabId: {tab}")

    try:
        snap = await client.snapshot(tab_id, user_id=user_id, include_screenshot=False)
        snapshot_text = snap.get("snapshot", "")
        title = snap.get("title", "")
        url_final = snap.get("url", url)

        # Truncate if too large for LLM context
        if len(snapshot_text) > max_snapshot_chars:
            snapshot_text = snapshot_text[:max_snapshot_chars] + "\n... [truncado por límite de contexto]"

        return {
            "status": "ok",
            "url": url_final,
            "title": title,
            "snapshot": snapshot_text,
            "tab_id": tab_id,
            "has_screenshot": False,
        }
    finally:
        try:
            await client.close_tab(tab_id, user_id=user_id)
        except Exception:
            pass


async def search_and_browse(
    query: str,
    user_id: str = "wallasapi_default",
    macro: str = "@google_search",
    max_results_pages: int = 3,
) -> Dict[str, Any]:
    """
    High-level helper: use search macro, open first result, get snapshot.
    Returns list of page snapshots from top search results.
    """
    client = get_browser_client()
    health = await client.health()
    if not health["ok"]:
        raise RuntimeError(f"Camofox no está disponible: {health.get('error', 'unknown')}")

    # Open a blank tab and run search macro
    tab = await client.open_tab("about:blank", user_id=user_id)
    tab_id = tab.get("tabId") or tab.get("id")
    if not tab_id:
        raise RuntimeError(f"Camofox no devolvió tabId: {tab}")

    try:
        nav = await client.navigate_macro(tab_id, macro=macro, query=query, user_id=user_id)
        # Get links on the search results page
        links_data = await client.links(tab_id, user_id=user_id)
        links_list = links_data.get("links", [])[:max_results_pages]

        results: List[Dict[str, Any]] = []
        for link in links_list:
            link_url = link.get("href") or link.get("url")
            if not link_url:
                continue
            # Open each result in its own tab
            try:
                sub_tab = await client.open_tab(link_url, user_id=user_id)
                sub_id = sub_tab.get("tabId") or sub_tab.get("id")
                if not sub_id:
                    continue
                try:
                    snap = await client.snapshot(sub_id, user_id=user_id)
                    results.append({
                        "url": link_url,
                        "title": snap.get("title", ""),
                        "snapshot": snap.get("snapshot", "")[:3000],
                    })
                finally:
                    await client.close_tab(sub_id, user_id=user_id)
            except Exception as e:
                results.append({"url": link_url, "error": str(e)})

        return {
            "status": "ok",
            "query": query,
            "macro": macro,
            "results": results,
            "search_tab_id": tab_id,
        }
    finally:
        try:
            await client.close_tab(tab_id, user_id=user_id)
        except Exception:
            pass
