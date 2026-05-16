# Changelog

All notable changes to WallasAPI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.1.0] — 2026-05-16

Coherence pass: the engine was already mature, but README, `.env.example`,
`requirements.txt`, and the codebase had drifted apart. This release realigns
everything so a fresh `git clone` runs cleanly and the documentation reflects
what the code actually does.

### Added

- **`/api/*` Ollama-compatible gateway** (`ollama_compat.py`). Any Ollama client
  pointed at `http://localhost:8001` now sees a unified catalog: WallasAPI cloud
  models plus the local Ollama daemon (if running). Endpoints: `/api/version`,
  `/api/tags`, `/api/show`, `/api/generate`, `/api/chat`. Configurable via
  `OLLAMA_UPSTREAM` and `WALLAS_OLLAMA_VERSION`.
- **`Advanced Features` section** in README documenting capabilities that
  already existed in code but were undiscoverable: Fork Mode
  (`/v1/chat/completions/fork`), Diligence Compare (`/v1/diligence/compare`),
  Web Search (`/v1/search/web`), Browser Automation via Camofox
  (`/v1/browser/*`), Circuit Breaker observability (`/v1/stats`), MCP Server
  (Model Context Protocol for Claude Desktop / Cursor / Windsurf), Anthropic-
  compatible `/v1/messages`, and the health dashboard.
- **`tests/` directory** with `conftest.py` so pytest can collect from the
  new location regardless of working directory.
- **`integrations/openclaw/`** (renamed from the ambiguously-named `cosa/`)
  containing the OpenClaw skill bundle, MCP config, and launch script.
- **Operational helpers** at the repo root: `restart.bat`, `stop.bat`,
  `start_minimal.bat`.
- **`WALLAS_MODELS_CACHE_TTL_SECONDS`** now honored by the model fetcher —
  stale on-disk caches refresh automatically after the TTL expires.
- **Documentation of all advertised but previously undocumented env vars**
  in `.env.example`: `SAMBANOVA_API_KEY`, `HUGGINGFACE_API_KEY`,
  `NVIDIA_API_KEY`, `WALLAS_PORT`, `WALLAS_HOST`, `WALLAS_OPENCLAW_MODE`,
  `WALLAS_SILENT_AGENT`, `WALLAS_MODELS_CACHE_TTL_SECONDS`,
  `OLLAMA_UPSTREAM`, `WALLAS_OLLAMA_VERSION`.

### Changed

- **README structure repaired.** The "Modo Ollama" block was previously nested
  inside `## Acknowledgments`, breaking the page render. It is now a first-
  class `## Ollama Mode (Unified Gateway)` section in English, placed before
  License. `## Acknowledgments` is back to a single coherent block at the
  end of the file.
- **Model counts unified.** Badges, title, and body now consistently say
  *"12+ providers · 600+ models"*. The contradictory "100+" and "650+"
  strings are gone.
- **SambaNova added** to the main Supported Providers table (it was
  previously only in the free-API-keys table, causing a visible discrepancy).
- **Virtual models table fixed** to match the actual IDs the code accepts:
  `auto`, `rapido`, `standard`, `razonamiento` (the README previously listed
  English aliases `fast` / `reasoning` that no longer exist in `VIRTUAL_MODELS`).
- **`X-Willaku-Tier` and `X-Willaku-Web-Search` headers** are now documented
  in the README Quick Usage section.
- **`requirements.txt` made executable from scratch.** Added the five
  packages that the codebase imports but never declared:
  `google-auth`, `google-auth-oauthlib`, `google-api-python-client`,
  `requests`, `rich`.
- **BITACORA consolidated.** `BITACORA.md` and `BITACORA_WALLAS.md` merged
  into a single chronological file sorted descending by date.
- **MCP server (`mcp_server.py`) HTTP mode** now uses `uvicorn.Server`
  directly and a `nest_asyncio` fallback, avoiding the
  `asyncio.run() cannot be called from a running event loop` error when
  the MCP HTTP mode is started inside an existing asyncio context.

### Fixed

- **Dead fallback path in `api_server.py`.** The previous heuristic resolved
  to a self-pointing directory but the `else` branch tried to import
  `.router_embedded`, `.config_embedded`, `.model_fetcher_embedded`,
  `.logger_embedded` — none of which exist anywhere in the tree. Replaced
  with direct imports.
- **Bare `except:` in `router.py`** swallowed `KeyboardInterrupt` and masked
  bugs in candidate-sorting. Now `except Exception as e` with a warning log.
- **Chat-title heuristic** (`"ERROR" in title`) used to discard legitimate
  titles containing the word ERROR (e.g. "Diagnóstico de ERROR 500" became
  "Nueva Conversación"). Now matches only on the error markers the router
  itself emits: `startswith(("ERROR", "[ERROR", "[Error"))`.
- **Version strings unified.** The FastAPI app declared `4.0.0-openclaw`
  while `/health` and `/` returned `4.1.0`. All three now agree on `4.1.0`.
- **App title rebranded** from `"WallasAPI-OpenClaw"` to
  `"WallasAPI - Your better and friendly AI router"`, with a description
  that mentions the three protocols (OpenAI · Anthropic · Ollama) and the
  circuit-breaker. Reflected in the OpenAPI schema served at `/docs`.

### Removed

- Duplicate / scratch / debris files: `README - copia.md`,
  `README - copia (2).md`, `api_server.py.backup.v3`, `_test_audio_routing.py`,
  `_test_fix.py`, `diagnose.py`, `diagnose2.py`, `test_for1..8.bat`,
  `cosa/wallasapi.zip`, and the old `BITACORA_WALLAS.md` (merged).

### Security

- Runtime state files (`last_request.json`, `reminders.json`, `settings.json`,
  `models_cache.json`, `free_models_report.json`, `*.backup.v*`) are now
  excluded by `.gitignore` so they cannot be accidentally committed.
- Pre-publish secret-scan of every tracked file against patterns for OpenAI,
  GitHub, Groq, Gemini, Cerebras, NVIDIA, and HuggingFace keys: zero matches.

### Verified

End-to-end smoke test against a live `python api_server.py` server:

| Endpoint | Result |
|---|---|
| `GET /health` | ✅ 12 providers, 649 models loaded, 267 free |
| `POST /v1/chat/completions` (`auto`, non-stream) | ✅ Routed to cerebras/llama3.1-8b |
| `POST /v1/chat/completions` (`rapido`, latency 1.3 s) | ✅ |
| `POST /v1/chat/completions` (`razonamiento`) | ✅ |
| `POST /v1/chat/completions` (streaming SSE) | ✅ keep-alive + chunks + `[DONE]` |
| `GET /api/version`, `GET /api/tags` | ✅ 623 tags exposed via Ollama protocol |
| `POST /api/chat` | ✅ Ollama-shaped response |
| `GET /v1/stats` | ✅ Circuit breaker state visible |
| `POST /v1/messages` (Anthropic-compat) | ✅ |

---

## [4.0.0] — 2026-04-26

Initial public release as WallasAPI (formerly `ai_services/`).

### Added

- Standalone `wallasAPI/` package, separated from the broader ProyectoIG
  monorepo so it can evolve independently.
- `/v1/embeddings` endpoint for IDE indexing (Cursor, Windsurf).
- `/v1/completions` (legacy) for tools that still speak the old OpenAI shape.
- Automatic model-alias mapping (e.g. `gpt-4o-2024-08-06` → router alias).

### Changed

- Default port moved from 8000 to **8001**.
- `/v1/models` response shape upgraded to satisfy strict autonomous agents.
- Console banner and documentation rebranded to "WallasAPI".

### Engine

- WallasRouter v3.1, 650+ models indexed across 12 providers.

---

[4.1.0]: https://github.com/wubjak/wallasapi/releases/tag/v4.1.0
[4.0.0]: https://github.com/wubjak/wallasapi/releases/tag/v4.0.0
