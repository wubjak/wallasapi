<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ Providers">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ Models">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>The Definitive Multi-Provider AI Routing Engine</strong></p>

<p align="center"><em>Built with sweat, determination, and a 2018 laptop, from a rented room, by <strong>Willen Ponce</strong></em></p>

---

## Why WallasAPI Exists: A Story That Matters

I wasn't born with a MacBook Pro M4. I don't have cloud servers funded by Silicon Valley investors. I don't have a team of 50 engineers behind me. **What I have is a 2018 laptop, a rented room that isn't mine, and an obsession: proving that from precarity, you can build something that competes with corporations.**

WallasAPI was born in stolen hours between worrying about rent, about the next meal, about sleeping at least four hours straight without waking up thinking about how much I owe. I had no money to pay for expensive APIs. I had no company backing me. I only had one obsessive question:

> **"Why should I depend on a single AI provider when the entire world of models is out there, many free, many better for specific tasks?"**

So I built it. **Line by line of Python. No fancy frameworks. No teams. No investors.** Just pure code, smart heuristics, and the desperate need to create something that works. Because when you have nothing to lose, every line of code is a bet against despair.

**WallasAPI is not just software. It is technological survival.** It is the router that doesn't charge you for being smart. It is the system that doesn't leave you hanging when OpenAI goes down, when your Claude API key expires, or when your favorite provider decides to raise prices. It knows when to use **Gemini** (free), when to use **Groq** (ultra-fast), when to use **DeepSeek R1** (deep reasoning), when to use your own **local Ollama** (100% private).

**And it does it all automatically.**

---

## What Is WallasAPI?

WallasAPI is a **unified routing engine** that connects your application, IDE, or agent with **12+ AI providers** (and growing) through a **single OpenAI-compatible API**.

You don't need to integrate 12 different SDKs. You don't need to memorize which model accepts images, which is free, which supports streaming, which has a 1-million-token context. **WallasAPI knows for you. And exposes it so your client discovers automatically.**

When you send a prompt, WallasAPI:
1. **Analyzes the content** (text, image, audio, PDF, video)
2. **Selects the optimal provider** based on capabilities, speed, availability, and cost
3. **Routes the request** automatically
4. **If the primary provider fails**, transparently falls back to the next without your user noticing
5. **Returns the response** in OpenAI-compatible format, with streaming if requested

**Your existing code works unchanged.** Just change the base URL.

---

## Features That Change the Rules

Each of these features was built because I needed it to survive as a developer without a budget:

### 1. Intelligent Multi-Provider Routing with Automatic Fallback
OpenAI fails? No drama. WallasAPI switches to **Gemini** in milliseconds. Groq goes down? Routes to **Cerebras** or **local Ollama** instantly. No single point of failure. Your application **never goes without a response.**

### 2. Real Streaming with Total Transparency
Responses arrive token by token in real time, exactly like OpenAI. But what if the primary provider fails mid-stream? **The fallback is completely transparent.** Your user doesn't notice a provider changed underneath.

### 3. Multimodal Support That Thinks for You
Text, images, audio, video, PDFs. Here's the magic: **the router decides WHO can process WHAT.** Want to send a PDF to Groq? WallasAPI knows Groq doesn't accept native files, so it automatically extracts text with OCR and sends it. Want to send a video to Gemini? Processes it natively without conversions. **You don't decide the provider. The content decides.**

### 4. Rich Metadata for Smart Clients
Every model exposes complete metadata: context window, pricing tier, tools, streaming, reasoning, input/output modalities, max images per request. Your IDE can ask: "give me only free vision models that accept native files" and WallasAPI responds filtered automatically.

### 5. Persistent Memory That Respects Your Privacy
Conversations with history saved locally in JSON. Syncable with **Obsidian** for those who live in interconnected notes. Your history doesn't go to the cloud unless you want it to.

### 6. Unified Image, Video, and Voice Generation
A single endpoint to create multimodal content from multiple providers:
- **Image**: Gemini, Pollinations (Flux, SDXL), HuggingFace, OpenAI DALL-E, NVIDIA NIM, local Ollama
- **Video**: Gemini, HuggingFace Spaces
- **Text-to-Speech (TTS)**: OpenAI, edge-tts with multiple voices

### 7. OCR with Fallback Chain
Extracts text from images and PDFs with **EasyOCR** -> **Mistral** -> **Gemini** -> **local Ollama**. If the first fails, tries the next. No image goes unread.

### 8. 100% Private Local Models via Ollama
Run **Llama 3, Mistral, Qwen, DeepSeek** completely free and private on your own machine. No API keys. No internet. No one reads your prompts.

### 9. Complete Google Integration
Drive, Calendar, Gmail with OAuth2. Local reminders that sync with Google Calendar. Project management with threads, files, and metadata.

---

## Rich Metadata System: The Brain We Built

When you have hundreds of models scattered across dozens of providers, the question isn't "which one do I use?" The question is: **"Does this model accept images? What's its context window? Is it free? Does it support tools? Can I send a native PDF or do I need to extract text first?"**

WallasAPI answers automatically with exact metadata for every model:

```json
{
  "context_window": 128000,
  "max_images_per_request": 5,
  "supports_tools": true,
  "supports_streaming": true,
  "supports_reasoning_stream": false,
  "input_modalities": ["text", "image", "audio"],
  "output_modalities": ["text"],
  "pricing_tier": "free",
  "provider_limits": {
    "max_images_per_request": 5,
    "supports_tools": true,
    "supports_streaming": true,
    "max_context_hint": 128000,
    "pricing": "free"
  }
}
```

### Automatic Heuristics Tested by 17 Tests

| Family | Context Window | Tools | Streaming | Vision | Audio | Native Files |
|---|---|---|---|---|---|---|
| Gemini 2.5 Pro | 1,000,000 | Yes | Yes | Yes | Yes | Yes |
| Gemini 1.5 Pro | 2,000,000 | Yes | Yes | Yes | Yes | Yes |
| GPT-4o / 4.1 | 128K - 1M | Yes | Yes | Yes | No | No |
| Claude 3 | 200,000 | Yes | Yes | Yes | No | No |
| Llama 3.3 (Groq) | 128,000 | Yes | Yes | Yes | No | No (auto shim) |
| DeepSeek R1 | 64,000 | Yes | Yes | No | No | No |
| Llama 3.1 (Cerebras) | 8,192 | No | Yes | No | No | No |
| Flux (Pollinations) | N/A | No | No | No | No | Image gen only |

**How it works:** Reads the model name, detects patterns (`vision`, `vl`, `audio`, `reasoning`, `r1`), consults provider limits, and builds metadata automatically. It's not magic. It's code written by hand at 3 AM on a 2018 laptop.

---

## API Endpoints

### Chat Completions (100% OpenAI-compatible)

| Endpoint | Method | Description |
|---|---|---|
| `POST /v1/chat/completions` | Chat | Completions with streaming. Supports virtual models: `auto`, `fast`, `standard`, `reasoning`. |
| `POST /v1/embeddings` | Embeddings | Multi-provider routing (NVIDIA, OpenAI, Ollama). |
| `POST /v1/tts` | TTS | Text-to-speech with multiple providers. |
| `POST /v1/images/generations` | Image | Unified image generation. |
| `POST /v1/videos/generations` | Video | Unified video generation. |

### Smart Metadata

| Endpoint | Description |
|---|---|
| `GET /v1/models` | List models with complete metadata. Filters: `?pricing=free`, `?capability=vision`, `?provider=groq`, `?search=llama`, `?modality=audio`. |
| `GET /v1/models/{id}` | Detailed metadata for a specific model. |
| `GET /v1/capabilities/summary` | Aggregated summary: how many free, vision, audio, reasoning, streaming, generation, native file models. |
| `GET /v1/providers` | Global metadata per provider: requires auth, supports vision/audio/native files, modalities, pricing. |

### Premium Services

| Endpoint | Description |
|---|---|
| `POST /v1/ocr/process` | OCR with fallback chain (EasyOCR -> Mistral -> Gemini -> Ollama). |
| `POST /v1/interpret` | Image analysis with textual description. |
| `POST /v1/sync/obsidian` | Memory sync with Obsidian. |
| `GET /v1/health` | System health check. |

---

## Virtual Models: Strategy, Not Provider

Instead of saying "use gpt-4o" and crossing your fingers, you use **virtual** models that the router resolves intelligently:

| Virtual | Strategy | Typical Providers |
|---|---|---|
| `auto` | Automatic selection by capability + speed + availability | The best available right now |
| `fast` | Minimum latency, instant responses | Groq, Cerebras |
| `standard` | Balance quality/speed/cost | Gemini, GPT-4o, Llama 70B |
| `reasoning` | Deep thinking before responding | DeepSeek R1, o1, o3, Gemini 2.5 Pro |

---

## Supported Providers

| Provider | Capabilities | Pricing |
|---|---|---|
| **Gemini** (Google) | Chat, vision, audio, video, native files, image/video generation | **Free** |
| **Groq** | Ultra-fast LLMs (Llama, Mixtral) | **Free** |
| **GitHub Models** | Free access to GPT-4o, o1, o3, Mistral, Llama, Cohere | **Free** |
| **OpenRouter** | Unified access (Claude, DeepSeek, Qwen, etc.) | Mixed |
| **Cohere** | Command R, Command R+ | Paid |
| **Mistral** | Mistral Large, Medium, Small | Paid |
| **Ollama** | Fully private local models | **Free** |
| **NVIDIA NIM** | GPU-optimized LLMs | Paid |
| **Cerebras** | Ultra-fast inference on proprietary hardware | **Free** |
| **Pollinations** | Image/video generation (Flux, etc.) | **Free** |
| **HuggingFace** | Community models | Mixed |
| **OpenAI** | GPT-4o, GPT-4.1, embeddings, TTS, DALL-E | Paid |

**Free + Fast + Private + Paid = All coexist.** You decide which to use. WallasAPI automatically decides which is best at any moment.

---

## Quick Install

### Windows (Recommended: Double-click `start.bat`)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/wallasapi.git
cd wallasapi

# 2. Double-click start.bat
#    - Creates virtual environment automatically
#    - Installs dependencies
#    - Starts server at http://localhost:8001

# Or manually:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

### Linux / macOS

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

Server starts at **http://localhost:8001**

Interactive docs (Swagger UI): **http://localhost:8001/docs**

---

## Configuration

Create a `.env` file in the project root with the API keys of the providers you want to use. **You don't need all of them.** WallasAPI works with whatever you have.

```env
# Free providers (recommended to start)
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
GITHUB_TOKEN=your_github_token_here

# Paid providers (optional)
OPENAI_API_KEY=your_openai_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
COHERE_API_KEY=your_cohere_key_here
MISTRAL_API_KEY=your_mistral_key_here
NVIDIA_API_KEY=your_nvidia_key_here

# Security (optional, for VPS deployment)
PROXY_API_KEY=your_secret_key_to_protect_endpoints

# Ollama requires no API key — runs locally for free
```

---

## Provider Registration: How to Get Free API Keys (Step by Step)

**IMPORTANT:** Every user must use THEIR OWN API key. **DO NOT share your `.env` file and DO NOT upload your keys to GitHub.** Getting free keys is quick and gives you full control.

### 100% Free Providers (Start Here)

| Provider | What it's for | How to register and get your key |
|---|---|---|
| **Gemini (Google)** | Gemini 2.0/2.5 Pro/Flash models with 1M-2M context, vision, audio, video, native files | 1. Go to [ai.google.dev](https://ai.google.dev)<br>2. Click "Get API key in Google AI Studio"<br>3. Sign in with your Google account<br>4. Go to the "Get API key" tab<br>5. Click "Create API key"<br>6. Copy the key and paste into `GEMINI_API_KEY=...` |
| **Groq** | Ultra-fast LLMs (Llama 3.3 70B, Mixtral, Gemma) with 100-300ms latency | 1. Go to [console.groq.com](https://console.groq.com)<br>2. Click "Sign Up" (email or Google/GitHub)<br>3. Go to the "API Keys" section<br>4. Click "Create API Key"<br>5. Copy the key and paste into `GROQ_API_KEY=...` |
| **GitHub Models** | Free access to GPT-4o, o1, o3, Mistral, Llama, Cohere | 1. You need a GitHub account (free)<br>2. Go to [github.com/settings/tokens](https://github.com/settings/tokens)<br>3. Click "Generate new token (classic)"<br>4. Check basic permissions (no special scopes needed)<br>5. Generate and copy the token<br>6. Paste into `GITHUB_TOKEN=...`<br>7. Also register at models: [github.com/marketplace/models](https://github.com/marketplace/models) |
| **OpenRouter** | Unified gateway to Claude, DeepSeek, Qwen, and 100+ models | 1. Go to [openrouter.ai](https://openrouter.ai)<br>2. Click "Sign Up" (email or Google/GitHub/Twitter)<br>3. Go to "Keys" in the side panel<br>4. Click "Create Key"<br>5. Copy the key and paste into `OPENROUTER_API_KEY=...`<br>6. Many models are free with generous rate limits |
| **Cerebras** | Ultra-fast inference on Cerebras hardware (Llama 3.1-8B) | 1. Go to [cloud.cerebras.ai](https://cloud.cerebras.ai)<br>2. Sign up with email<br>3. Go to the "API Keys" section<br>4. Generate a new key<br>5. Paste into your `.env` |
| **Pollinations** | Image generation (Flux, SDXL) and video completely free | 1. Go to [pollinations.ai](https://pollinations.ai)<br>2. No API key required for basic use<br>3. For API: register and get key from docs<br>4. Note: WallasAPI uses Pollinations' public endpoint which requires no auth |
| **Ollama** | 100% private local models (Llama, Mistral, Qwen, DeepSeek) | 1. Download [ollama.com](https://ollama.com) and install<br>2. Run `ollama run llama3.1`<br>3. WallasAPI auto-detects Ollama at `localhost:11434`<br>4. **NO API key needed — 100% free and private** |

### Paid Providers (Optional, if you need more)

| Provider | What it's for | How to register |
|---|---|---|
| **OpenAI** | GPT-4o, GPT-4.1, DALL-E, Whisper, embeddings, TTS | [platform.openai.com](https://platform.openai.com) — Sign up, add credit/prepaid card |
| **Mistral AI** | Mistral Large, Medium, Pixtral | [console.mistral.ai](https://console.mistral.ai) — Registration with $5 free initial credit |
| **Cohere** | Command R, Command R+ | [cohere.com](https://cohere.com) — Registration with free trial credit |
| **NVIDIA NIM** | Enterprise GPU-optimized LLMs | [build.nvidia.com](https://build.nvidia.com) — Registration with free initial credit |

### Security Tips

- **NEVER upload your `.env` to GitHub.** Use `.gitignore` to exclude it.
- **Use environment variables** in production instead of `.env` files.
- **Rotate your keys** periodically from each provider's dashboard.
- **Monitor usage** in each provider's dashboard to not exceed free limits.

With just **Gemini + Groq + GitHub Models** you have access to dozens of extremely powerful models without paying a cent. Start with those three.

---

## Quick Usage

### Basic chat with virtual model

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="anything-local"  # or your PROXY_API_KEY if configured
)

# Choose strategy, not provider
response = client.chat.completions.create(
    model="auto",  # WallasAPI picks the best available provider
    messages=[{"role": "user", "content": "Explain general relativity"}]
)
print(response.choices[0].message.content)
```

### Streaming with automatic fallback

```python
for chunk in client.chat.completions.create(
    model="fast",  # Prioritizes speed (Groq, Cerebras)
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
):
    print(chunk.choices[0].delta.content or "", end="")
```

### Discover free vision models

```bash
curl "http://localhost:8001/v1/models?pricing=free&capability=vision"
```

### Check if a model supports native files

```bash
curl "http://localhost:8001/v1/providers"
# Gemini: supports_native_files = true (send PDFs directly)
# Groq: supports_native_files = false (auto OCR)
```

### Generate an image

```python
image = client.images.generate(
    model="flux",  # Pollinations, free
    prompt="A cat astronaut in space, pixel art style"
)
```

---

## Project Structure

```
wallasAPI/
├── api_server.py          # FastAPI server with OpenAI-compatible endpoints
├── router.py              # Intelligent routing engine with fallback
├── config.py              # Configuration, metadata schema, heuristics
├── model_fetcher.py         # Dynamic model discovery
├── file_utils.py           # OCR, text extraction, file processing
├── memory.py              # Persistent conversation memory
├── google_service.py      # Google OAuth2 integration
├── reminders.py           # Reminder system
├── projects.py            # Project management
├── settings.py            # User preferences
├── logger.py              # Centralized logging
├── providers/             # Individual providers
│   ├── huggingface.py
│   └── ...
├── start.bat              # Windows startup script (double-click)
├── requirements.txt       # Dependencies
├── LICENSE                # Custom license
└── README.md              # This file
```

---

## License

This project is licensed under a custom MIT-based license.

**You can use, modify, distribute, and build upon it freely.** The only real condition is that you keep attribution to **Willen Ponce** as the original author.

**A personal request (not legally required):** If you use WallasAPI in any project, product, service, or deployment — commercial or not — I would deeply appreciate if you send me an email at **wubjak@protonmail.ch** telling me you're using WallasAPI. You don't need to share technical details or proprietary information. A simple **"Hey, I'm using WallasAPI for X, thanks for building it"** is enough to make the day of a developer who built this on a 2018 laptop from a rented room much better.

See the `LICENSE` file for the full text.

---

## Donations: Keep This Alive

This project has no sponsors. It has no Silicon Valley investors. It has no marketing team. It has a 2018 laptop, a rented room, and code that works.

**If WallasAPI saved you hours of integration, helped you build something cool, or you simply believe free software should exist without depending on billionaire corporations:**

### Your direct support changes absolutely everything:

- **PayPal**: [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi**: [ko-fi.com/wubjak](https://ko-fi.com/wubjak) — Every coffee counts.
- **Email**: wubjak@protonmail.ch

**Yape / Plin (Peru) — Number: 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**Crypto Wallets:**

| Currency | Address |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"Before they kick me out of the house, so I can have breakfast, pay my debts, and sleep at least 4 hours straight without waking up thinking about how much I owe, every contribution counts. Thank you for using WallasAPI."* — **Willen Ponce**

---

## Acknowledgments

- To the creators of FastAPI, for making APIs in Python something beautiful.
- To Google, Meta, DeepSeek, Mistral, and all providers offering free models.
- To the open-source community, proving that free software can compete with any corporation.
- **To you**, for reading this far and considering using WallasAPI.

---

<p align="center">
  <strong>WallasAPI</strong> — <em>One API to rule them all.<br>
  Built from precarity, with the determination of someone who has nothing to lose.</em>
</p>
