<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ Anbieter">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ Modelle">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>Die Definitive Multi-Anbieter KI-Routing-Engine</strong></p>

<p align="center"><em>Gebaut mit Schweiß, Entschlossenheit und einem Laptop aus 2018, aus einem gemieteten Zimmer, von <strong>Willen Ponce</strong></em></p>

---

## Warum WallasAPI Existiert: Eine Geschichte, die zahlt

Ich bin nicht mit einem MacBook Pro M4 geboren. Ich habe keine Cloud-Server, die von Silicon-Valley-Investoren finanziert werden. Ich habe kein Team von 50 Ingenieuren hinter mir. **Was ich habe, ist ein Laptop aus 2018, ein gemietetes Zimmer, das mir nicht gehort, und eine Obsession: zu beweisen, dass man aus der Prekaritat etwas bauen kann, das mit Unternehmen konkurriert.**

WallasAPI wurde in gestohlenen Stunden geboren, zwischen Sorgen um die Miete, um die nachste Mahlzeit, um mindestens vier Stunden am Stuck schlafen zu konnen, ohne aufzuwachen und daran zu denken, wie viel ich schulde. Ich hatte kein Geld, um teure APIs zu bezahlen. Ich hatte kein Unternehmen, das mich unterstutzte. Ich hatte nur eine obsessiv Frage:

> **"Warum sollte ich von einem einzigen KI-Anbieter abhangig sein, wenn die ganze Welt von Modellen da draußen ist, viele kostenlos, viele besser fur spezifische Aufgaben?"**

Also habe ich es gebaut. **Zeile fur Zeile Python. Ohne fancy Frameworks. Ohne Teams. Ohne Investoren.** Nur reiner Code, intelligente Heuristiken, und die verzweifelte Notwendigkeit, etwas zu schaffen, das funktioniert.

**WallasAPI ist nicht nur Software. Es ist technologisches Uberleben.** Es ist der Router, der Sie nicht dafur berechnet, intelligent zu sein. Es ist das System, das Sie nicht im Stich lasst, wenn OpenAI ausfallt, wenn Ihr Claude-API-Key ablauft oder wenn Ihr Lieblingsanbieter die Preise erhoht.

---

## Was ist WallasAPI?

WallasAPI ist eine **unifizierte Routing-Engine**, die Ihre Anwendung, IDE oder Ihren Agenten mit **uber 12 KI-Anbietern** uber eine **einzelne OpenAI-kompatible API** verbindet.

Wenn Sie einen Prompt senden, WallasAPI:
1. **Analysiert den Inhalt** (Text, Bild, Audio, PDF, Video)
2. **Wahlt den optimalen Anbieter** basierend auf Fahigkeiten, Geschwindigkeit, Verfugbarkeit und Kosten
3. **Leitet die Anfrage** automatisch weiter
4. **Falls der primare Anbieter ausfallt**, transparentes Fallback zum nachsten
5. **Gibt die Antwort** im OpenAI-kompatiblen Format zuruck, mit Streaming wenn angefordert

**Ihr bestehender Code funktioniert ohne Anderungen.** Andern Sie einfach die Basis-URL.

---

## Hauptfunktionen

- **Intelligentes Multi-Anbieter Routing mit automatischem Fallback**
- **Echtes Streaming mit totaler Transparenz**
- **Multimodale Unterstutzung** — Text, Bilder, Audio, Video, PDFs
- **Reiche Metadaten** — Context Window, Pricing Tier, Tools, Streaming, Modalitaten
- **Persistenter Speicher** — Lokaler JSON-Verlauf, synchronisierbar mit Obsidian
- **Vereinigte Generierung** — Bild, Video, TTS von mehreren Anbietern
- **OCR mit Fallback-Kette** — EasyOCR -> Mistral -> Gemini -> lokaler Ollama
- **100% private lokale Modelle** — Uber Ollama
- **Vollstandige Google-Integration** — Drive, Calendar, Gmail mit OAuth2

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|---|---|---|
| `POST /v1/chat/completions` | Chat | Completions mit Streaming. Virtuelle Modelle: `auto`, `fast`, `standard`, `reasoning`. |
| `POST /v1/embeddings` | Embeddings | Multi-Anbieter Routing. |
| `POST /v1/tts` | TTS | Text zu Sprache. |
| `POST /v1/images/generations` | Bild | Vereinigte Bildgenerierung. |
| `POST /v1/videos/generations` | Video | Vereinigte Videogenerierung. |
| `GET /v1/models` | Auflisten | Modelle mit vollstandigen Metadaten. Filter: `?pricing=free`, `?capability=vision`. |
| `GET /v1/models/{id}` | Details | Detaillierte Metadaten eines Modells. |
| `GET /v1/capabilities/summary` | Zusammenfassung | Wie viele kostenlos, mit Vision, Audio, Reasoning, etc. |
| `GET /v1/providers` | Anbieter | Globale Metadaten pro Anbieter. |

---

## Schnelle Installation

### Windows (Empfohlen: Doppelklick auf `start.bat`)

```bash
git clone https://github.com/ihr-benutzer/wallasapi.git
cd wallasapi
# Doppelklick auf start.bat
```

### Linux / macOS

```bash
git clone https://github.com/ihr-benutzer/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

Server startet auf **http://localhost:8001**

Interaktive Dokumentation: **http://localhost:8001/docs**

---

## Konfiguration

Erstellen Sie eine `.env` Datei mit den API-Keys der Anbieter, die Sie verwenden mochten. **Sie brauchen nicht alle.**

```env
# Kostenlose Anbieter (empfohlen zum Starten)
GEMINI_API_KEY=ihr_key_hier
GROQ_API_KEY=ihr_key_hier
GITHUB_TOKEN=ihr_token_hier

# Bezahlte Anbieter (optional)
OPENAI_API_KEY=ihr_key_hier
OPENROUTER_API_KEY=ihr_key_hier
```

---

## Lizenz

Projekt unter angepasster MIT-Lizenz. Behalten Sie die Zuordnung zu **Willen Ponce** bei.

**Personliche Bitte:** Wenn Sie WallasAPI verwenden, senden Sie eine E-Mail an **wubjak@protonmail.ch** und sagen Sie mir, dass Sie es nutzen. Ein einfaches "Hallo, ich benutze WallasAPI fur X, danke fur den Bau" reicht aus, um den Tag eines Entwicklers zu machen, der dies auf einem Laptop aus 2018 gebaut hat.

Siehe Datei `LICENSE` fur den vollstandigen Text.

---

## Spenden: Das am Leben Erhalten

Dieses Projekt hat keine Sponsoren. Keine Silicon-Valley-Investoren. Es hat einen Laptop aus 2018, ein gemietetes Zimmer, und Code, der funktioniert.

**Wenn WallasAPI Ihnen Stunden der Integration erspart oder Ihnen geholfen hat, etwas Cooles zu bauen:**

- **PayPal** : [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi** : [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **E-Mail** : wubjak@protonmail.ch

**Yape / Plin (Peru) — Nummer : 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**Crypto-Wallets :**

| Wahrung | Adresse |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"Bevor sie mich aus dem Haus werfen, damit ich fruhstucken kann, meine Schulden bezahlen, und mindestens 4 Stunden am Stuck schlafen kann, ohne aufzuwachen und daran zu denken, wie viel ich schulde, zahlt jeder Beitrag. Danke, dass Sie WallasAPI nutzen."* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>Eine API, um sie alle zu beherrschen.<br>
  Gebaut aus der Prekaritat, mit der Entschlossenheit dessen, der nichts zu verlieren hat.</em>
</p>
