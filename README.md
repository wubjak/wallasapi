<div align="center">

<img src="logos/socialbanner.png" alt="WallasAPI — 12+ AI Providers · 600+ Models · One API" width="100%">

# One API. 12+ AI Providers. 600+ Models. Zero Vendor Lock-in.

**The unified, OpenAI-compatible router that automatically picks the best AI provider for every request — and falls back transparently when one fails.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Providers](https://img.shields.io/badge/Providers-12+-orange.svg?style=for-the-badge)](#supported-providers)
[![Models](https://img.shields.io/badge/Models-600+-purple.svg?style=for-the-badge)](#supported-providers)

[![Sponsor](https://img.shields.io/badge/💛_Sponsor-Willen_Ponce-ff69b4?style=for-the-badge)](#donations--why-this-matters)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/wubjak)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/wubjak)

**[English](README.md) · [Español](docs/i18n/README.es.md) · [中文](docs/i18n/README.zh.md) · [Português](docs/i18n/README.pt.md) · [Français](docs/i18n/README.fr.md) · [Deutsch](docs/i18n/README.de.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md) · [Русский](docs/i18n/README.ru.md) · [العربية](docs/i18n/README.ar.md)**

</div>

---

> ## A Note from the Author — Please Read This
>
> Hi, I'm **Willen Ponce**. I built WallasAPI alone, in stolen hours between worrying about rent and the next meal, on a 2018 laptop, in a rented room in Peru that isn't mine.
>
> I have **no investors**. **No team**. **No company**. Just code, determination, and the desperate need to prove that you don't need Silicon Valley money to build something useful.
>
> If WallasAPI saves you even one hour of integration work, please consider:
> - ⭐ **[Starring this repo](https://github.com/wubjak/wallasapi)** — costs you nothing, helps me enormously
> - 💛 **[Buying me a coffee on Ko-fi](https://ko-fi.com/wubjak)** or **[via PayPal](https://paypal.me/wubjak)** — even $1 changes my day
> - 📧 **Sending an email to `wubjak@protonmail.ch`** — just say "I'm using WallasAPI for X". That's it. That's enough.
>
> [**Skip to the donation section →**](#donations--why-this-matters)

---

## Why WallasAPI Exists

You're building with AI in 2026. You face a real problem:

- 🔴 OpenAI goes down → your app dies
- 🔴 Your Claude API key expires → users complain
- 🔴 Gemini is free but doesn't accept your file format → manual conversion
- 🔴 You want to use a free model for cheap tasks and a powerful one for hard tasks → you write 200 lines of switching logic
- 🔴 Each provider has a different SDK, different format, different errors

**WallasAPI solves all of this with one OpenAI-compatible endpoint.** Send a request, and it:

1. **Analyzes the content** (text, image, audio, PDF, video)
2. **Picks the optimal provider** based on capabilities, speed, cost, and current availability
3. **Routes the request** automatically
4. **Falls back transparently** if the primary provider fails — your user never sees the error
5. **Returns the response** in standard OpenAI format, with streaming if you asked for it

**Your existing OpenAI SDK code works unchanged.** Just point it at `http://localhost:8001/v1`.

---

## What Makes This Different

Every feature here was built because **I needed it to ship products without a budget**:

| Feature | Why it matters |
|---|---|
| 🔄 **Multi-provider routing with auto-fallback** | If OpenAI goes down, Gemini takes over in milliseconds. Your app keeps working. |
| 🌊 **Real streaming with transparent fallback** | Token-by-token responses. If the primary provider dies mid-stream, fallback is invisible to the user. |
| 🧠 **Content-aware multimodal routing** | Send a PDF to Groq? It auto-OCRs it. Send a video to Gemini? Native processing. **You don't pick the provider — the content does.** |
| 📊 **Rich metadata for smart clients** | Every model exposes context window, pricing, tools support, modalities. Filter: `?pricing=free&capability=vision`. |
| 💾 **Persistent local memory** | Conversations saved as JSON, optionally synced to **Obsidian**. Your data stays yours. |
| 🎨 **Unified image/video/voice generation** | One endpoint, multiple providers (Flux, DALL-E, Pollinations, edge-tts, Gemini). |
| 📄 **OCR with fallback chain** | EasyOCR → Mistral → Gemini → local Ollama. No image goes unread. |
| 🔒 **100% private local models via Ollama** | Run Llama, Mistral, Qwen, DeepSeek offline. Zero data leaves your machine. |
| 🔗 **Google integration** | Drive, Calendar, Gmail with OAuth2. Project management with threads. |

---

## Supported Providers

| Provider | Capabilities | Pricing |
|---|---|---|
| **Gemini** (Google) | Chat, vision, audio, video, native files, image/video gen | **Free** |
| **Groq** | Ultra-fast Llama, Mixtral | **Free** |
| **GitHub Models** | GPT-4o, o1, o3, Mistral, Llama, Cohere | **Free** |
| **OpenRouter** | Claude, DeepSeek, Qwen + 100 more | Mixed |
| **Cerebras** | Ultra-fast Llama on proprietary HW | **Free** |
| **SambaNova** | Fast Llama 3.1/3.2/3.3, DeepSeek, Qwen with vision | **Free** |
| **Pollinations** | Flux, SDXL image gen | **Free** |
| **Ollama** | Local Llama, Mistral, Qwen, DeepSeek | **Free** |
| **HuggingFace** | Community models, Spaces video | Mixed |
| **Cohere** | Command R, Command R+ | **Free** (trial/compatibility tier) |
| **Mistral AI** | Mistral Large, Medium, Pixtral | **Free** (small/medium/pixtral) |
| **NVIDIA NIM** | GPU-optimized enterprise LLMs | **Free** (developer tier) |
| **OpenAI** | GPT-4o, GPT-4.1, DALL-E, Whisper, embeddings, TTS | **Mixed** (free via GitHub Models, paid direct) |

**With just the free tiers across these providers, you have access to 600+ state-of-the-art models without paying a cent. WallasAPI automatically filters which specific models are free via the `FREE` capability flag.**

---

## Quick Install (60 seconds)

### Windows — Just double-click `start.bat`

```bash
git clone https://github.com/wubjak/wallasapi.git
cd wallasapi
# Double-click start.bat
# Server is up at http://localhost:8001
```

### Linux / macOS / WSL2

```bash
# Prerequisite (Debian/Ubuntu/WSL2 only — install once).
# libgl1 + libglib2.0-0 are needed by easyocr/opencv. lsof lets start.sh free port 8001.
sudo apt install -y python3 python3-venv python3-pip libgl1 libglib2.0-0 lsof

# IMPORTANT: clone with the capitalized name so the package import path matches
# (the codebase imports `wallasAPI` and Linux filesystems are case-sensitive).
git clone https://github.com/wubjak/wallasapi.git wallasAPI
cd wallasAPI
chmod +x start.sh
./start.sh
```

> **Running on WSL2 alongside another agent (Hermes, OpenClaw, etc.)?**
> WallasAPI binds to `0.0.0.0:8001`, so it's reachable from inside WSL at
> `http://localhost:8001/v1` **and** from the Windows host at the same URL
> (WSL2 forwards localhost automatically). If your Ollama daemon lives on the
> Windows side, set `OLLAMA_UPSTREAM=http://host.docker.internal:11434` in
> `.env`. Skip `./install-launcher.sh` on headless WSL — it needs a GUI
> terminal emulator. Point your agent at `http://localhost:8001/v1` (OpenAI
> wire) or `http://localhost:8001/v1/messages` (Anthropic wire) — both
> protocols share the same port.

Or manually if you prefer to see each step:

```bash
git clone https://github.com/wubjak/wallasapi.git wallasAPI
cd wallasAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python api_server.py
```

**Optional — install the `wallasapi` CLI** so you get one command for everything (`start`, `stop`, `update`, `status`, `logs`) instead of `cd`-ing into the repo:

```bash
cd wallasAPI
mkdir -p ~/.local/bin && ln -sf "$PWD/wallasapi" ~/.local/bin/wallasapi
# If ~/.local/bin isn't on your PATH yet:
#   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

Then from anywhere:

```bash
wallasapi              # start in foreground (Ctrl+C to stop)
wallasapi start        # start in background, logs to /tmp/wallas.log
wallasapi stop         # stop the running server
wallasapi update       # git pull + refresh deps + restart (the most useful one)
wallasapi status       # is it running? on which commit? how many models?
wallasapi logs         # tail -f the background log
```

**Optional GUI launcher** (Linux desktops with Activities / app menu):

```bash
cd wallasAPI
./install-launcher.sh
```

After this, double-clicking the "WallasAPI" icon (or searching it in Activities) starts the server inside a terminal window. A companion "Stop WallasAPI" entry is also installed. Skip this on headless WSL — it needs a GUI terminal emulator.

<details>
<summary>Troubleshooting</summary>

- **`apt install python3.X-venv` fails** — your distro may not yet package the
  venv module for very new Python versions (e.g. 3.14). Fall back to a stable
  version: `sudo apt install -y python3.12 python3.12-venv` and use
  `python3.12 -m venv .venv` instead.
- **`error: externally-managed-environment` (PEP 668)** — you tried to `pip
  install` outside a venv. Always activate `.venv` first (`source
  .venv/bin/activate`) before running `pip install`.
- **No `sudo` available** — use the modern Python toolchain:
  ```bash
  pip install --user --break-system-packages uv
  uv venv .venv && source .venv/bin/activate
  uv pip install -r requirements.txt
  ```
- **`ModuleNotFoundError: No module named 'wallasAPI'`** — you cloned into a
  lowercase `wallasapi/` directory. Linux is case-sensitive: rename it
  (`mv wallasapi wallasAPI`) or re-clone with the explicit target name shown
  above.

</details>

Interactive Swagger UI: **http://localhost:8001/docs**

---

## Quick Usage

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="anything-local"
)

# Don't pick a provider. Pick a strategy.
response = client.chat.completions.create(
    model="auto",  # WallasAPI picks the best free provider available NOW
    messages=[{"role": "user", "content": "Explain quantum entanglement"}]
)
print(response.choices[0].message.content)
```

**Virtual models you can use instead of guessing provider names:**

| Virtual model | Strategy |
|---|---|
| `auto` | Best available right now |
| `rapido` | Lowest latency (Groq, Cerebras, SambaNova) |
| `standard` | Quality/speed/cost balance |
| `razonamiento` | Deep thinking (DeepSeek R1, o1, o3, Gemini 2.5 Pro) |
| `agentico` | Reliable multi-step tool callers (Claude Sonnet+, GPT-4o+, Llama 3.3 70B, Mistral Large, DeepSeek V3, Gemini 2.5+) — use for agentic loops where the model must invoke tools several times per turn |
| `vista` | Free vision-capable models (Llama 3.2 Vision, Gemini Flash, Pixtral, Qwen-VL) — use when the request includes images |

**Strategy via header** — instead of overriding `model`, you can keep your existing model and add `X-Willaku-Tier: rapido|standard|razonamiento|agentico|vista|auto` to any request. Add `X-Willaku-Web-Search: true` to enrich the prompt with live DuckDuckGo results. See [`DOCUMENTACION_COMPLETA.md`](DOCUMENTACION_COMPLETA.md) for the full header reference.

---

## API Endpoints

OpenAI-compatible:
- `POST /v1/chat/completions` — chat with streaming
- `POST /v1/embeddings` — multi-provider embeddings
- `POST /v1/images/generations` — Flux, DALL-E, etc.
- `POST /v1/videos/generations` — Gemini, HuggingFace
- `POST /v1/tts` — text-to-speech

WallasAPI exclusive:
- `GET /v1/models?pricing=free&capability=vision` — filtered model discovery
- `GET /v1/models/{id}` — full metadata for any model
- `GET /v1/capabilities/summary` — aggregate stats
- `GET /v1/providers` — provider-level capabilities
- `POST /v1/ocr/process` — OCR with auto-fallback
- `POST /v1/sync/obsidian` — sync conversations to your vault

Anthropic-compatible:
- `POST /v1/messages` — drop-in endpoint for Claude Code, Claude Desktop, and other tools that speak the Anthropic protocol. Internally routed to whichever provider is best for the request.

---

## Advanced Features

Built-in capabilities that go beyond a vanilla OpenAI proxy:

### 🍴 Fork Mode — race N models, return the winner

`POST /v1/chat/completions/fork` runs the same prompt against multiple providers in parallel and returns the best result (or all of them, with `return_all=true`). Each candidate is scored by latency, success, and length. Great for benchmarking or for getting an answer fast when you don't care which provider produces it.

```bash
curl -X POST http://localhost:8001/v1/chat/completions/fork \
  -H "Content-Type: application/json" \
  -d '{"model":"rapido","messages":[{"role":"user","content":"haiku about routing"}],"max_parallel":3}'
```

### ⚖️ Diligence Compare — head-to-head provider report

`POST /v1/diligence/compare` ranks providers for a specific task, returning latency, score, and a text preview for each. Useful for picking the right provider for a recurring workload.

```bash
curl -X POST http://localhost:8001/v1/diligence/compare \
  -d '{"task":"Summarize quantum computing in 2 lines","criteria":"calidad","max_parallel":4}'
```

### 🌐 Web Search — DuckDuckGo · Google CSE · SerpAPI fallback

`POST /v1/search/web` returns real-time web results from whichever backend is reachable. Combined with `X-Willaku-Web-Search: true` on chat requests, the search context gets injected into the system prompt automatically.

### 🦊 Browser Automation (Camofox)

When the optional `camofox-browser` service is running on `:9377`, WallasAPI exposes stealth scraping endpoints: `POST /v1/browser/open`, `/v1/browser/act`, `/v1/browser/search`, `/v1/browser/summarize`, `/v1/browser/youtube/transcript`. Opens a real browser tab, navigates, clicks, types, and returns a clean snapshot the LLM can consume.

### 📊 Circuit Breaker Observability

`GET /v1/stats` shows every `provider/model` circuit: success count, fail count, EMA latency, current cooldown, last error. Lets you see in real time which providers are flaky and how the router is reacting.

### 🔌 MCP Server (Model Context Protocol)

[`mcp_server.py`](mcp_server.py) exposes WallasAPI as an MCP server for Claude Desktop, Cursor, and Windsurf. Models, search, OCR, and browser tools become first-class MCP capabilities your IDE/agent can call directly. Default port `:8002` (SSE mode).

### 🎯 Service Health Dashboard

`GET /health` reports the status of WallasAPI itself, Camofox, and the MCP server in one call — useful for monitoring or for IDE plugins that want to gracefully degrade when a side-service is offline.

---

## Configuration

Copy `.env.example` to `.env` and fill in **only the keys you have**. WallasAPI works with whatever you give it.

```env
# 100% free providers (start here)
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
GITHUB_TOKEN=your_token

# Optional paid
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

### How to get free API keys (step by step)

| Provider | Where | Time |
|---|---|---|
| **Gemini** | [ai.google.dev](https://ai.google.dev) → Get API key | 1 min |
| **Groq** | [console.groq.com](https://console.groq.com) → API Keys | 1 min |
| **GitHub Models** | [github.com/settings/tokens](https://github.com/settings/tokens) → classic token | 2 min |
| **Sambanova** | [cloud.sambanova.ai](https://cloud.sambanova.ai) → API Keys | 2 min |
| **Cerebras** | [cloud.cerebras.ai](https://cloud.cerebras.ai) → API Keys | 2 min |
| **Mistral AI** | [console.mistral.ai](https://console.mistral.ai) → API Keys | 1 min |
| **NVIDIA NIM** | [build.nvidia.com](https://build.nvidia.com) → API Keys | 2 min |
| **Cohere** | [cohere.com](https://cohere.com) → Trial/compatibility API key | 1 min |
| **HuggingFace** | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → Access Token | 1 min |
| **Pollinations** | No API key needed — totally free | 0 min |
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) → Keys (filter `:free` models) | 1 min |
| **Ollama** | [ollama.com](https://ollama.com) — install + `ollama run llama3.1` | 5 min |

**Total: ~15 minutes to get free access to 600+ state-of-the-art models.**

---

## Ollama Mode (Unified Gateway)

WallasAPI also speaks the **Ollama** protocol on the same port. Point any Ollama client at `http://localhost:8001` and you'll see a unified catalog: WallasAPI cloud models **plus** local models from the real Ollama daemon (if it's running at `localhost:11434`).

Exposed endpoints:

- `GET  /api/version`
- `GET  /api/tags` — union of cloud models + local Ollama tags
- `POST /api/show` — per-model metadata
- `POST /api/generate` — completions (NDJSON streaming)
- `POST /api/chat` — multi-turn chat (NDJSON streaming)

Environment variables:

- `OLLAMA_UPSTREAM` — URL of the real Ollama daemon (default `http://localhost:11434`). If it doesn't respond, the catalog gracefully falls back to cloud-only.
- `WALLAS_OLLAMA_VERSION` — string returned by `/api/version` (default `0.1.0-wallas`).

Examples:

```bash
curl http://localhost:8001/api/tags
curl http://localhost:8001/api/chat -d '{
  "model":"gpt-4o-mini",
  "messages":[{"role":"user","content":"hi in one word"}],
  "stream":false
}'
```

If the requested `model` matches a local Ollama tag, the request is proxied byte-for-byte to the daemon. If it matches a WallasAPI cloud model, it goes through the internal `AIRouter` and the response is translated to Ollama's shape.

---

## License

MIT-based custom license. **Use, modify, distribute, deploy commercially — all free.** The only ask: keep the attribution to **Willen Ponce**.

**One personal request (not legally required):** If you use WallasAPI in any project, please send a one-line email to **wubjak@protonmail.ch**. A simple *"Hey, using WallasAPI for X"* literally makes my week. I built this alone and it would mean a lot to know it's helping someone.

See [`LICENSE`](LICENSE) for full text.

---

## Donations — Why This Matters

<div align="center">

### 🍞 Right now I cannot afford basic food. This is not a metaphor.

</div>

I'm not going to dress this up. I'm a developer in Peru who built this entire project — **17 modules, 12+ provider integrations, 1500+ lines of routing logic, OCR fallback chains, multimodal handling, persistent memory** — alone, on a 2018 laptop, in a rented room.

**I have no income right now.** I'm behind on rent. I haven't eaten properly in days while finishing this. I'm publishing it free because I believe open-source matters more than I matter, and because maybe — just maybe — someone reading this will find it useful and decide to help me eat tomorrow.

### What your donation actually does

| Amount | What it means for me |
|---|---|
| **$1** | A real bread + egg meal. Not symbolic. Real. |
| **$5** | A full day of food while I keep coding. |
| **$20** | A week where I don't have to choose between food and electricity. |
| **$100** | One month of rent. Stops me from being evicted. |
| **$400** | Six months of stability. I can dedicate that time fully to making WallasAPI better for you. |

**Every single dollar is documented in my conscience and remembered with gratitude.**

### How to send help

<div align="center">

[![PayPal](https://img.shields.io/badge/PayPal-paypal.me/wubjak-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/wubjak)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-ko--fi.com/wubjak-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/wubjak)
[![Email](https://img.shields.io/badge/Email-wubjak@protonmail.ch-8B89CC?style=for-the-badge&logo=protonmail&logoColor=white)](mailto:wubjak@protonmail.ch)

</div>

**Yape / Plin (Peru) — Number: `980 702 580`**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin">
</p>

**Crypto wallets:**

| Currency | Address |
|---|---|
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

### Can't donate? You can still help (it's free)

- ⭐ **Star this repo** — it costs you nothing and pushes WallasAPI into more developers' feeds
- 🐦 **Share it** on Twitter/X, LinkedIn, HackerNews, Reddit r/LocalLLaMA, your dev community
- 🐛 **Open an issue** if you find a bug or have a feature request
- 💬 **Send the email** to `wubjak@protonmail.ch` — it's not transactional, it's human

> *"I built WallasAPI because I refused to accept that being broke meant being unable to ship great software. If it helps you ship something — that's already a victory I'll never forget. If it helps me eat tomorrow — that's a victory neither of us will forget."* — **Willen Ponce**

---

## Acknowledgments

- The teams at **FastAPI**, **Google**, **Meta**, **DeepSeek**, **Mistral**, and every provider offering free tiers — you made this possible
- The **open-source community** — proof that we don't need billion-dollar valuations to build great things
- **You** — for reading this far. Whether you donate, star, share, or just use it: thank you

---

<div align="center">

### WallasAPI — One API to route them all

*Built from precarity. Maintained with stubbornness. Shared with hope.*

**[⭐ Star](https://github.com/wubjak/wallasapi) · [💛 Donate](#donations--why-this-matters) · [📧 Email me](mailto:wubjak@protonmail.ch)**

</div>
