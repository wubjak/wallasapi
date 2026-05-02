"""
WallasAPI — MCP Server (Model Context Protocol)
===============================================

Expone todas las capacidades de WallasAPI como tools MCP para Gravedad,
Claude Desktop, o cualquier cliente MCP-compatible.

Tools disponibles:
  - wallas_web_search         → búsqueda web dual backend
  - wallas_fork_completion      → ejecución paralela multi-modelo
  - wallas_diligence_compare    → comparar APIs para una tarea
  - wallas_browser_browse       → abrir URL vía camofox
  - wallas_browser_search       → buscar con macro vía camofox
  - wallas_browser_youtube      → transcript de YouTube
  - wallas_get_models           → listar modelos disponibles
  - wallas_get_stats            → estado de providers (circuit breaker)

Uso:
  python mcp_server.py           # stdio (default, para Claude Desktop)
  python mcp_server.py --http    # SSE en puerto 8002

Configuración en cliente MCP:
  {
    "mcpServers": {
      "wallasapi": {
        "command": "python",
        "args": ["D:/ProyectoIG/wallasAPI/mcp_server.py"]
      }
    }
  }
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx

# ─── Configuración ────────────────────────────────────────────────────────────
WALLAS_BASE = os.getenv("WALLASAPI_URL", "http://localhost:8001")
WALLAS_KEY = os.getenv("WALLASAPI_KEY", "wallasapi-local")


# ═════════════════════════════════════════════════════════════════════════════
#  Intentar importar SDK MCP oficial; si no está, usar fallback mínimo
# ═════════════════════════════════════════════════════════════════════════════
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import SseServerTransport
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel,
    )
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("[WARN] SDK MCP no instalado. Ejecuta: pip install mcp", file=sys.stderr)


# ─── Helper HTTP ────────────────────────────────────────────────────────────

async def _call_wallas(method: str, path: str, json_body: Optional[Dict] = None) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {"Authorization": f"Bearer {WALLAS_KEY}"}
        url = f"{WALLAS_BASE}{path}"
        if method == "GET":
            r = await client.get(url, headers=headers)
        elif method == "POST":
            r = await client.post(url, headers=headers, json=json_body)
        else:
            raise ValueError(f"Método no soportado: {method}")
        r.raise_for_status()
        return r.json()


# ─── Tool handlers ──────────────────────────────────────────────────────────

TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "wallas_web_search",
        "description": (
            "Búsqueda web en tiempo real con fallback automático entre DuckDuckGo, "
            "Google Custom Search y SerpAPI. Ideal para precios, noticias, datos actuales."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
                "max_results": {"type": "integer", "default": 10},
                "backend": {
                    "type": "string",
                    "enum": ["auto", "duckduckgo", "google_cse", "serpapi"],
                    "default": "auto",
                    "description": "Backend preferido. 'auto' prueba DuckDuckGo primero y hace fallback.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "wallas_fork_completion",
        "description": (
            "Ejecuta la MISMA tarea en múltiples modelos en paralelo y devuelve "
            "el mejor resultado (o todos para comparar). Útil cuando la respuesta es crítica."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "default": "auto", "description": "Virtual model: auto, rapido, standard, razonamiento"},
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                    "description": "Lista de mensajes OpenAI-style. Mínimo 1 mensaje user.",
                },
                "max_parallel": {"type": "integer", "default": 3, "description": "Cuántos modelos ejecutar en paralelo (máx 5)"},
                "return_all": {"type": "boolean", "default": False, "description": "Si true, devuelve todos los resultados ordenados"},
                "web_search": {"type": "boolean", "default": False, "description": "Si true, enriquece con contexto web antes de responder"},
            },
            "required": ["messages"],
        },
    },
    {
        "name": "wallas_diligence_compare",
        "description": (
            "Compara en tiempo real qué API/modelo cumple mejor una diligencia específica. "
            "Devuelve ranking con latencia, score y preview de cada modelo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "La tarea/diligencia a evaluar"},
                "system_prompt": {"type": "string", "default": "Eres un asistente experto."},
                "max_parallel": {"type": "integer", "default": 3},
                "criteria": {"type": "string", "default": "calidad", "enum": ["calidad", "velocidad", "costo"]},
            },
            "required": ["task"],
        },
    },
    {
        "name": "wallas_browser_browse",
        "description": (
            "Abre una URL en navegador headless stealth (camofox) y devuelve "
            "snapshot accesible + título. Útil para leer páginas con paywall o JS."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL completa a abrir"},
                "user_id": {"type": "string", "default": "wallasapi_default"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "wallas_browser_search",
        "description": (
            "Busca con macro de camofox (@google_search, @youtube_search, etc.) "
            "y extrae snapshots de los top resultados."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "macro": {"type": "string", "default": "@google_search", "enum": ["@google_search", "@youtube_search", "@amazon_search", "@reddit_subreddit"]},
                "max_results_pages": {"type": "integer", "default": 3},
                "user_id": {"type": "string", "default": "wallasapi_default"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "wallas_browser_youtube",
        "description": "Extrae transcript de un video de YouTube vía camofox (usa yt-dlp si está disponible).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL del video de YouTube"},
                "languages": {"type": "array", "items": {"type": "string"}, "default": ["es", "en"]},
            },
            "required": ["url"],
        },
    },
    {
        "name": "wallas_get_models",
        "description": "Lista todos los modelos disponibles en WallasAPI, incluyendo virtuales y gratis.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "wallas_get_stats",
        "description": (
            "Devuelve métricas en tiempo real: circuit breaker, latencias EMA, "
            "cooldowns y errores recientes de cada provider."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


async def _handle_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ejecuta la tool solicitada vía HTTP a WallasAPI."""
    try:
        if name == "wallas_web_search":
            payload = {
                "query": arguments["query"],
                "max_results": arguments.get("max_results", 10),
                "backend": arguments.get("backend", "auto"),
            }
            data = await _call_wallas("POST", "/v1/search/web", payload)
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "wallas_fork_completion":
            payload = {
                "model": arguments.get("model", "auto"),
                "messages": arguments["messages"],
                "max_parallel": arguments.get("max_parallel", 3),
                "return_all": arguments.get("return_all", False),
                "web_search": arguments.get("web_search", False),
            }
            data = await _call_wallas("POST", "/v1/chat/completions/fork", payload)
            # Si return_all, formatear bonito; si no, extraer winner
            if payload.get("return_all"):
                text = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                meta = data.get("fork_metadata", {})
                winner = meta.get("winner", {})
                text = (
                    f"**Winner:** {winner.get('provider', '?')}/{winner.get('model', '?')}\n"
                    f"**Latencia:** {winner.get('latency_ms', '?')} ms  |  **Score:** {winner.get('score', '?')}\n\n"
                    f"{content}\n\n"
                    f"_Otros intentos:_ {len(meta.get('others', []))} modelos paralelos."
                )
            return [TextContent(type="text", text=text)]

        elif name == "wallas_diligence_compare":
            payload = {
                "task": arguments["task"],
                "system_prompt": arguments.get("system_prompt", "Eres un asistente experto."),
                "max_parallel": arguments.get("max_parallel", 3),
                "criteria": arguments.get("criteria", "calidad"),
            }
            data = await _call_wallas("POST", "/v1/diligence/compare", payload)
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "wallas_browser_browse":
            payload = {
                "url": arguments["url"],
                "user_id": arguments.get("user_id", "wallasapi_default"),
            }
            data = await _call_wallas("POST", "/v1/browser/summarize", payload)
            snap = data.get("snapshot", "")
            title = data.get("title", "")
            text = f"**Título:** {title}\n**URL final:** {data.get('url', arguments['url'])}\n\n{snap[:8000]}"
            if len(snap) > 8000:
                text += "\n\n_[Contenido truncado por límite de contexto]_"
            return [TextContent(type="text", text=text)]

        elif name == "wallas_browser_search":
            payload = {
                "query": arguments["query"],
                "macro": arguments.get("macro", "@google_search"),
                "max_results_pages": arguments.get("max_results_pages", 3),
                "user_id": arguments.get("user_id", "wallasapi_default"),
            }
            data = await _call_wallas("POST", "/v1/browser/search", payload)
            results = data.get("results", [])
            lines = [f"Búsqueda: **{arguments['query']}** (macro: {payload['macro']})\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"\n--- Resultado {i} ---\n**URL:** {r.get('url', '?')}\n**Título:** {r.get('title', '?')}\n\n{r.get('snapshot', '')[:2000]}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "wallas_browser_youtube":
            payload = {
                "url": arguments["url"],
                "languages": arguments.get("languages", ["es", "en"]),
            }
            data = await _call_wallas("POST", "/v1/browser/youtube/transcript", payload)
            transcript = data.get("transcript", "")
            video_title = data.get("video_title", "")
            return [TextContent(
                type="text",
                text=f"**Video:** {video_title}\n\n```\n{transcript[:10000]}\n```"
            )]

        elif name == "wallas_get_models":
            data = await _call_wallas("GET", "/v1/models")
            models = data.get("data", [])
            free = [m for m in models if m.get("metadata", {}).get("pricing_tier") == "free"]
            lines = [
                f"Total modelos: {len(models)}  |  Gratis: {len(free)}\n",
                "**Modelos virtuales:** auto, rapido, standard, razonamiento\n",
                "**Top gratis:**",
            ]
            for m in free[:15]:
                lines.append(f"- `{m.get('id', '?')}` ({m.get('provider', '?')})")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "wallas_get_stats":
            data = await _call_wallas("GET", "/v1/stats")
            providers = data.get("providers", [])
            lines = ["**Estado de providers**\n"]
            for p in providers:
                status = "🟢 OK" if p.get("is_open") else "🔴 CAÍDO"
                lines.append(
                    f"- `{p.get('provider', '?')}/{p.get('model', '?')}` → {status}  "
                    f"(latencia EMA: {p.get('avg_latency_ms', '?')} ms, "
                    f"fallos: {p.get('fail_count', 0)}, "
                    f"éxitos: {p.get('success_count', 0)})"
                )
            return [TextContent(type="text", text="\n".join(lines))]

        else:
            return [TextContent(type="text", text=f"Tool desconocida: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"[ERROR] {name}: {e}")]


# ─── MCP Server setup ───────────────────────────────────────────────────────

async def _main_stdio():
    if not _MCP_AVAILABLE:
        print("[FATAL] Instala el SDK MCP: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = Server("wallasapi")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [Tool(**t) for t in TOOLS_SCHEMA]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> List[Any]:
        return await _handle_tool(name, arguments)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="wallasapi",
                server_version="4.1.0",
                capabilities=server.get_capabilities(),
            ),
        )


async def _main_http(port: int = 8002):
    """Experimental: SSE transport para clientes HTTP."""
    if not _MCP_AVAILABLE:
        print("[FATAL] Instala el SDK MCP: pip install mcp", file=sys.stderr)
        sys.exit(1)

    from fastapi import FastAPI
    from mcp.server.sse import SseServerTransport

    app = FastAPI()
    transport = SseServerTransport("/messages/")

    @app.get("/sse")
    async def sse_endpoint(request):
        async with transport.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            server = Server("wallasapi")

            @server.list_tools()
            async def list_tools() -> List[Tool]:
                return [Tool(**t) for t in TOOLS_SCHEMA]

            @server.call_tool()
            async def call_tool(name: str, arguments: Any) -> List[Any]:
                return await _handle_tool(name, arguments)

            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="wallasapi",
                    server_version="4.1.0",
                    capabilities=server.get_capabilities(),
                ),
            )

    import uvicorn
    print(f"[MCP HTTP] WallasAPI MCP Server en http://0.0.0.0:{port}/sse")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WallasAPI MCP Server")
    parser.add_argument("--http", action="store_true", help="Modo HTTP/SSE en vez de stdio")
    parser.add_argument("--port", type=int, default=8002, help="Puerto para modo HTTP")
    args = parser.parse_args()

    if args.http:
        asyncio.run(_main_http(args.port))
    else:
        asyncio.run(_main_stdio())
