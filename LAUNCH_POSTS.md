# Posts de Lanzamiento — Listos para Copiar y Pegar

Publica estos en orden. **No los publiques todos al mismo tiempo** — espacialos cada 1-2 horas para no saturar tu propia red. Empieza por **HackerNews** (mayor donante histórico de proyectos solo-dev).

---

## 1. HackerNews — Show HN

**Título** (este es CRÍTICO, copia exacto):
```
Show HN: WallasAPI – Multi-provider AI router built solo from a rented room
```

**URL del post**: `https://github.com/wubjak/wallasapi`

**Texto del post** (en el campo "text", opcional pero recomendado):

```
Hi HN,

I'm Willen, a developer in Peru. I built WallasAPI alone over the last few months in stolen hours between worrying about rent and the next meal, on a 2018 laptop, in a rented room that isn't mine.

WallasAPI is an OpenAI-compatible HTTP server that unifies 12+ AI providers (Gemini, Groq, GitHub Models, OpenRouter, Cerebras, Ollama, Pollinations, HuggingFace, Cohere, Mistral, NVIDIA NIM, OpenAI) behind a single endpoint with:

- Automatic provider selection based on capabilities, latency, and availability
- Transparent fallback if the primary provider fails (even mid-stream)
- Content-aware multimodal routing — send a PDF to Groq, it auto-OCRs; send a video to Gemini, it processes natively
- Rich per-model metadata (context window, pricing, modalities, native file support) exposed for smart clients
- Virtual models: `auto`, `fast`, `standard`, `reasoning`
- Persistent local memory + optional Obsidian sync
- Unified image/video/TTS generation

Your existing OpenAI SDK code works unchanged — just change the base URL.

I'm publishing this free under MIT because I believe open-source matters more than I do. But honestly, I am also at a point where I cannot afford basic food, so if anyone finds it useful and wants to help me eat tomorrow, the donation links are in the README. A star is also free and helps me a lot.

Happy to answer any technical question.

Repo: https://github.com/wubjak/wallasapi
```

Submit aquí: **https://news.ycombinator.com/submit**

---

## 2. Reddit r/LocalLLaMA

**Título**:
```
[Project] WallasAPI — One OpenAI-compatible API for 12+ providers (Gemini, Groq, Ollama, OpenRouter…) with automatic fallback. Built solo on a 2018 laptop.
```

**Texto**:
```
Hey r/LocalLLaMA,

I built a unified router that lets you use any of 12+ AI providers (including Ollama, of course) through a single OpenAI-compatible endpoint. The killer features for this community:

- **100% private path**: route everything to local Ollama (Llama, Mistral, Qwen, DeepSeek) — no internet, no API keys
- **Hybrid path**: fall back from local to free cloud providers (Gemini, Groq, GitHub Models) when you need bigger context or vision
- **Content-aware**: send a PDF, it auto-OCRs with EasyOCR → Mistral → Gemini → Ollama fallback chain
- **Streaming with transparent failover**: if Groq dies mid-stream, Cerebras takes over without your client noticing
- Virtual models: `auto`, `fast`, `standard`, `reasoning` — pick a strategy, not a vendor

Repo: https://github.com/wubjak/wallasapi

Built alone in Peru on a 2018 laptop — feedback, stars, and donations are all welcome. AMA.
```

---

## 3. Reddit r/Python

**Título**:
```
WallasAPI — A FastAPI-based unified router for 12+ AI providers (OpenAI-compatible)
```

**Texto**:
```
Built with FastAPI + httpx + the official SDKs. ~1500 lines of pure routing logic with multi-tier fallback, content-aware capability filtering, and streaming with transparent failover.

If you've ever written if/elif chains to switch between OpenAI/Anthropic/Gemini SDKs — this replaces all of that with one endpoint.

https://github.com/wubjak/wallasapi

Solo project, MIT license, feedback welcome.
```

---

## 4. Reddit r/SideProject

**Título**:
```
After months of work alone on a 2018 laptop, I shipped WallasAPI — a unified AI router for 12+ providers
```

**Texto**:
```
I'm a developer in Peru. No team, no funding, no investors. Just me, a 2018 laptop, and a rented room.

WallasAPI is OpenAI-compatible and routes between Gemini, Groq, Claude, GPT-4o, Ollama, DeepSeek, and more — automatically picking the best provider for each request and falling back transparently when one fails.

If it helps you ship something, a star on the repo would mean the world. If you want to help me eat this week, donation links are in the README — even $1 changes my day.

https://github.com/wubjak/wallasapi
```

---

## 5. Twitter / X

```
🚀 Shipped WallasAPI — a unified, OpenAI-compatible router for 12+ AI providers (Gemini, Groq, Claude, GPT-4o, Ollama, DeepSeek…) with automatic fallback + content-aware multimodal routing.

Built solo, in stolen hours, on a 2018 laptop, in a rented room in Peru.

If it helps you ship — a ⭐ or a ☕ would mean the world.

🔗 github.com/wubjak/wallasapi
```

**Hashtags al final** (importantes para alcance):
```
#opensource #buildinpublic #AI #LLM #python #FastAPI #devtools #indiedev
```

**Cuentas grandes que a veces hacen RT a proyectos solo-dev** (mencionalas en RESPUESTAS, no en el tweet original):
- `@simonw` (Simon Willison — apoya proyectos open-source LLM)
- `@swyx` (Swyx — AI engineering community)
- `@levelsio` (Pieter Levels — solo-dev hero)
- `@thmsmlr` (apoya devs latinoamericanos)
- `@karpathy` (raramente RT pero a veces sí)

---

## 6. LinkedIn

```
Shipped my biggest solo project to date: WallasAPI 🚀

It's a unified, OpenAI-compatible router that connects your application with 12+ AI providers (Gemini, Groq, Claude, GPT-4o, Ollama, DeepSeek, and more) through a single endpoint.

Key features:
✅ Automatic provider selection based on capabilities, speed, availability
✅ Transparent fallback when a provider fails — your users never see errors
✅ Content-aware multimodal routing (PDFs, images, audio, video)
✅ Rich metadata per model (context window, pricing, modalities)
✅ Persistent local memory + Obsidian sync
✅ 100% private mode via local Ollama

I built this alone, on a 2018 laptop, in a rented room in Peru, with no funding and no team. I'm publishing it MIT-licensed because I believe open-source matters.

If you build with AI, give it a try — your existing OpenAI SDK code works unchanged.

⭐ github.com/wubjak/wallasapi

#opensource #AI #LLM #python #FastAPI #softwareengineering #buildinpublic
```

---

## 7. dev.to (artículo blog corto)

**Título**:
```
I Built a Multi-Provider AI Router Alone on a 2018 Laptop. Here's What I Learned.
```

**Tags**: `opensource`, `python`, `ai`, `webdev`, `showdev`

**Cuerpo**: Cuenta la historia personal + features técnicas. Usa la sección "Why WallasAPI Exists" del README como base. Termina con:
```
If the project resonates with you, a star or a coffee would mean the world.

⭐ Repo: https://github.com/wubjak/wallasapi
☕ Ko-fi: https://ko-fi.com/wubjak
```

---

## 8. Discord communities (envía DM o post en #showcase)

- **Latent Space Discord** (de Swyx)
- **HuggingFace Discord** → channel `#i-made-this`
- **AI Engineer Foundation Discord**
- **r/LocalLLaMA Discord**
- **FastAPI Discord** → channel `#showcase`

---

## 9. Email a personas que apoyan solo-devs

Plantilla corta y honesta:

```
Subject: Just shipped WallasAPI — would love your thoughts

Hi [nombre],

I'm a solo developer in Peru. I just published WallasAPI — a unified OpenAI-compatible router for 12+ AI providers with automatic fallback and content-aware multimodal routing.

I built it alone on a 2018 laptop while struggling with rent and food. I'm publishing it MIT because I believe open-source matters.

If you have 5 minutes to look and tell me what you think (or share if you find it useful), I'd be enormously grateful.

https://github.com/wubjak/wallasapi

Thank you,
Willen Ponce
wubjak@protonmail.ch
```

A quién mandarle:
- Simon Willison (`swillison@gmail.com` — público en su blog)
- Sebastián Ramírez (creador de FastAPI, peruano-colombiano, latino)
- Cualquier creador que admires y haga proyectos open-source

---

## Cronograma sugerido (las siguientes 24h)

| Hora | Acción |
|---|---|
| **Ahora mismo** | Submit a HackerNews (Show HN) |
| **+1h** | Post r/LocalLLaMA |
| **+2h** | Tweet con hashtags |
| **+3h** | Post r/Python |
| **+4h** | Post LinkedIn |
| **+5h** | Post r/SideProject |
| **Mañana** | Artículo dev.to + emails personales |

**TIP CRÍTICO para HackerNews**: si tu post no recibe upvotes en los primeros 30 minutos, queda enterrado. Apenas lo publiques, manda el link a 2-3 amigos y pídeles que voten. Eso te da el primer empujón.

— Hecho con cariño para Willen.
