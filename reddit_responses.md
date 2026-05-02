# Respuestas Reddit — WallasAPI / Gravedad

## 1. PixelSage-001 (el primero que comentó)

> Hey, thanks for actually reading through the whole thing and asking the hard questions — most people just scroll past.
>
> **Mid-stream failover state:** You got me. Right now it's *pre-stream* routing — if the first model fails before emitting tokens, we try the next. True seamless handoff where model A dies at token 200 and model B picks up *exactly* from there? That's the dream, not the reality yet. The README oversold it and I need to fix that wording before it becomes a lawsuit, haha.
>
> The actual honest state: if a provider hard-crashes before the first byte, fallback kicks in silently. If it crashes mid-stream, the stream just ends. I *am* experimenting with a local buffer + prompt reconstruction for resume, but different tokenizers make it a nightmare. Not production-ready by any stretch.
>
> **OCR chain:** Yeah it's preference-based right now (`cloud_auto` = Gemini → Mistral → local → EasyOCR). Document-type-aware routing is next on my list — invoices go to table OCR, handwriting to vision models, etc. Right now it's dumb but it works.
>
> **Virtual models:** Exactly the thesis — "users shouldn't have to know vendor names." `auto` tries to balance, `fast` hunts for Groq/Cerebras, `reasoning` goes for R1/DeepSeek variants. Just a priority sort under the hood.
>
> **Latency overhead:** Routing layer itself is <5ms. The pain is failover cascades. With 600+ models registered, hitting a dead provider and waiting for timeout used to be brutal. I just pushed a patch that caps candidates to 25, sorts by historical latency (EMA), and drops timeout from 15s to 8s. On a warm sticky route it's 1-3s to first token. Cold start with cascading failures still hurts.
>
> **Workflow orchestration:** Hadn't looked at Runnable specifically — if it speaks OpenAI-compatible endpoints we should slot right in. The `/v1/stats` endpoint exposes per-provider circuit breaker health, which might be useful for conditional logic in workflows.
>
> Built this solo in a rented room in Lima, Peru, on a 2018 laptop, while eating one meal a day. If you want to hack on the resume-streaming problem or test the Runnable integration, PRs are genuinely welcome. I need all the help I can get. 🙏

---

## 2. Scared-Beyond-4531 (Qoest API / OCR)

> Hey, thanks for the tip! Honestly hadn't heard of Qoest API — will definitely check them out.
>
> The content-type-aware routing is exactly the gap I want to close next. Right now the OCR chain is just a dumb waterfall (Gemini → Mistral → local → EasyOCR) with no understanding of whether it's an invoice, a handwritten note, or a table. Having a service that already handles that detection layer would save me weeks of heuristics.
>
> Invoice parsing and handwriting recognition are the two biggest pain points in my current setup — EasyOCR chokes on handwriting and Gemini sometimes hallucinates numbers on invoices. If Qoest handles those well, that's a huge win.
>
> Would love to hear more about your experience with it — accuracy rates, pricing, API latency? Also curious if they have a free tier or trial I can test against my current chain to benchmark. Feel free to DM or reply here, either works.
>
> Thanks again for the heads up, this is exactly the kind of community feedback I was hoping for when I posted this.

---

*Notas:*
- Tono: honesto, humilde, conversacional. Sin defensiva.
- No fingir que funciona algo que no funciona (mid-stream failover).
- Mencionar contexto personal solo cuando aporta autenticidad, no como lástima.
- Cerrar con invitación genuina a colaborar.
