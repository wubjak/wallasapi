<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ Fournisseurs">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ Modeles">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>Le Moteur de Routage Multi-Fournisseur Definitif</strong></p>

<p align="center"><em>Construit avec de la sueur, de la determination et un ordinateur portable de 2018, dans une chambre louee, par <strong>Willen Ponce</strong></em></p>

---

## Pourquoi WallasAPI Existe : Une Histoire qui Compte

Je ne suis pas ne avec un MacBook Pro M4. Je n'ai pas de serveurs cloud finances par des investisseurs de Silicon Valley. Je n'ai pas une equipe de 50 ingenieurs derriere moi. **Ce que j'ai, c'est un ordinateur portable de 2018, une chambre louee qui n'est pas a moi, et une obsession : prouver qu'on peut construire depuis la precarite quelque chose qui rivalise avec les entreprises.**

WallasAPI est ne dans les heures volees entre les soucis du loyer, du prochain repas, de pouvoir dormir au moins quatre heures d'affilee sans se reveiller en pensant a combien je dois. Je n'avais pas d'argent pour payer des API cheres. Je n'avais pas d'entreprise qui me soutenait. Je n'avais qu'une question obsessionnelle :

> **"Pourquoi devrais-je dependre d'un seul fournisseur d'IA quand le monde entier de modeles est la dehors, beaucoup gratuits, beaucoup meilleurs pour des taches specifiques ?"**

Alors je l'ai construit. **Ligne par ligne de Python. Sans frameworks luxueux. Sans equipes. Sans investisseurs.** Juste du code pur, des heuristiques intelligentes, et le besoin desespere de creer quelque chose qui fonctionne.

**WallasAPI n'est pas seulement un logiciel. C'est la survie technologique.** C'est le routeur qui ne vous facture pas pour etre intelligent. C'est le systeme qui ne vous laisse pas en plan quand OpenAI tombe, quand votre cle API de Claude expire, ou quand votre fournisseur prefere decide d'augmenter les prix.

---

## Qu'est-ce que WallasAPI ?

WallasAPI est un **moteur de routage unifie** qui connecte votre application, IDE ou agent avec **plus de 12 fournisseurs d'IA** via une **API unique 100% compatible OpenAI**.

Quand vous envoyez un prompt, WallasAPI :
1. **Analyse le contenu** (texte, image, audio, PDF, video)
2. **Selectionne le fournisseur optimal** base sur les capacites, la vitesse, la disponibilite et le cout
3. **Route la requete** automatiquement
4. **Si le fournisseur principal echoue**, effectue un fallback transparent vers le suivant
5. **Retourne la reponse** au format compatible OpenAI, avec streaming si demande

**Votre code existant fonctionne sans changements.** Changez simplement l'URL de base.

---

## Fonctionnalites Principales

- **Routage Intelligent Multi-Fournisseur avec Fallback Automatique**
- **Streaming Reel avec Transparence Totale**
- **Support Multimodal** — Texte, images, audio, video, PDFs
- **Metadonnees Enrichies** — Context window, pricing tier, outils, streaming, modalites
- **Memoire Persistante** — Historique local JSON, synchronisable avec Obsidian
- **Generation Unifiee** — Image, video, TTS depuis multiples fournisseurs
- **OCR avec Chaine de Fallback** — EasyOCR -> Mistral -> Gemini -> Ollama local
- **Modeles Locaux 100% Prives** — Via Ollama
- **Integration Google Complete** — Drive, Calendar, Gmail avec OAuth2

---

## Endpoints API

| Endpoint | Methode | Description |
|---|---|---|
| `POST /v1/chat/completions` | Chat | Completions avec streaming. Modeles virtuels : `auto`, `fast`, `standard`, `reasoning`. |
| `POST /v1/embeddings` | Embeddings | Routage multi-fournisseur. |
| `POST /v1/tts` | TTS | Texte vers parole. |
| `POST /v1/images/generations` | Image | Generation d'images unifiee. |
| `POST /v1/videos/generations` | Video | Generation de videos unifiee. |
| `GET /v1/models` | Lister | Modeles avec metadonnees completes. Filtres : `?pricing=free`, `?capability=vision`. |
| `GET /v1/models/{id}` | Details | Metadonnees detaillees d'un modele. |
| `GET /v1/capabilities/summary` | Resume | Combien gratuits, avec vision, audio, reasoning, etc. |
| `GET /v1/providers` | Fournisseurs | Metadonnees globales par fournisseur. |

---

## Installation Rapide

### Windows (Recommande : Double-clic sur `start.bat`)

```bash
git clone https://github.com/votre-utilisateur/wallasapi.git
cd wallasapi
# Double-clic sur start.bat
```

### Linux / macOS

```bash
git clone https://github.com/votre-utilisateur/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

Serveur demarre sur **http://localhost:8001**

Documentation interactive : **http://localhost:8001/docs**

---

## Configuration

Creez un fichier `.env` avec les cles API des fournisseurs que vous souhaitez utiliser. **Vous n'avez pas besoin de toutes.**

```env
# Fournisseurs gratuits (recommandes pour commencer)
GEMINI_API_KEY=votre_cle_ici
GROQ_API_KEY=votre_cle_ici
GITHUB_TOKEN=votre_token_ici

# Fournisseurs payants (optionnels)
OPENAI_API_KEY=votre_cle_ici
OPENROUTER_API_KEY=votre_cle_ici
```

---

## Licence

Projet sous licence MIT personnalisee. Gardez l'attribution a **Willen Ponce**.

**Demande personnelle :** Si vous utilisez WallasAPI, envoyez un email a **wubjak@protonmail.ch** pour me dire que vous l'utilisez. Un simple "Bonjour, j'utilise WallasAPI pour X, merci de l'avoir construit" suffit a faire la journee d'un developpeur qui a construit ceci sur un ordinateur de 2018.

Voir le fichier `LICENSE` pour le texte complet.

---

## Dons : Garder Ceci En Vie

Ce projet n'a pas de sponsors. Pas d'investisseurs de Silicon Valley. Il a un ordinateur de 2018, une chambre louee, et du code qui fonctionne.

**Si WallasAPI vous a fait economiser des heures d'integration ou vous a aide a construire quelque chose de cool :**

- **PayPal** : [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi** : [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **Email** : wubjak@protonmail.ch

**Yape / Plin (Perou) — Numero : 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**Portefeuilles Crypto :**

| Monnaie | Adresse |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"Avant qu'on me mette dehors, pour pouvoir prendre mon petit-dejeuner, payer mes dettes, et dormir au moins 4 heures d'affilee sans me reveiller en pensant a combien je dois, chaque contribution compte. Merci d'utiliser WallasAPI."* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>Une API pour les gouverner tous.<br>
  Construite depuis la precarite, avec la determination de celui qui n'a rien a perdre.</em>
</p>
