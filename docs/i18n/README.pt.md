<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ Provedores">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ Modelos">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>O Motor de Roteamento Multi-Provedor Definitivo</strong></p>

<p align="center"><em>Construido com suor, determinacao e um notebook de 2018, de um quarto alugado, por <strong>Willen Ponce</strong></em></p>

---

## Por que WallasAPI Existe: Uma Historia que Importa

Eu nao nasci com um MacBook Pro M4. Nao tenho servidores na nuvem financiados por investidores de Silicon Valley. Nao tenho uma equipe de 50 engenheiros. **O que eu tenho e um notebook de 2018, um quarto alugado que nao e meu, e uma obsessao: provar que da precariedade se pode construir algo que compete com corporacoes.**

WallasAPI nasceu nas horas roubadas entre preocupacoes com o aluguel, com a proxima refeicao, com conseguir dormir pelo menos quatro horas seguidas sem acordar pensando em quanto devo. Nao tinha dinheiro para pagar APIs caras. Nao tinha uma empresa me apoiando. So tinha uma pergunta obsessiva:

> **"Por que deveria depender de um unico provedor de IA quando o mundo inteiro de modelos esta ai fora, muitos gratuitos, muitos melhores para tarefas especificas?"**

Entao eu construi. **Linha por linha de Python. Sem frameworks luxuosos. Sem equipes. Sem investidores.** Apenas codigo puro, heuristicas inteligentes, e a necessidade desesperada de criar algo que funcione.

**WallasAPI nao e apenas software. E sobrevivencia tecnologica.** E o roteador que nao cobra por ser inteligente. E o sistema que nao te deixa na mao quando a OpenAI cai, quando sua chave API do Claude expira, ou quando seu provedor favorito decide aumentar os precos.

---

## O que e WallasAPI?

WallasAPI e um **motor de roteamento unificado** que conecta sua aplicacao, IDE ou agente com **mais de 12 provedores de IA** atraves de uma **unica API 100% compativel com OpenAI**.

Quando voce envia um prompt, WallasAPI:
1. **Analisa o conteudo** (texto, imagem, audio, PDF, video)
2. **Seleciona o provedor otimo** baseado em capacidades, velocidade, disponibilidade e custo
3. **Roteia a requisicao** automaticamente
4. **Se o provedor primario falha**, faz fallback transparente para o proximo
5. **Devolve a resposta** no formato compativel com OpenAI, com streaming se solicitado

**Seu codigo existente funciona sem mudancas.** Basta mudar a URL base.

---

## Recursos Principais

- **Roteamento Inteligente Multi-Provedor com Fallback Automatico** — Se um cai, troca em milissegundos
- **Streaming Real com Transparencia Total** — Respostas token a token, com fallback invisivel
- **Suporte Multimodal** — Texto, imagens, audio, video, PDFs. O roteador decide quem processa o que
- **Metadados Enriquecidos** — Cada modelo expoe context window, pricing tier, ferramentas, streaming, modalidades
- **Memoria Persistente** — Historico local em JSON, sincronizavel com Obsidian
- **Geracao Unificada** — Imagem (Gemini, Pollinations, HuggingFace, DALL-E, NVIDIA), Video, TTS
- **OCR com Cadeia de Fallback** — EasyOCR -> Mistral -> Gemini -> Ollama local
- **Modelos Locais 100% Privados** — Via Ollama (Llama, Mistral, Qwen, DeepSeek)
- **Integracao Google Completa** — Drive, Calendar, Gmail com OAuth2

---

## Endpoints da API

| Endpoint | Metodo | Descricao |
|---|---|---|
| `POST /v1/chat/completions` | Chat | Completions com streaming. Modelos virtuais: `auto`, `fast`, `standard`, `reasoning`. |
| `POST /v1/embeddings` | Embeddings | Roteamento multi-provedor. |
| `POST /v1/tts` | TTS | Texto para voz. |
| `POST /v1/images/generations` | Imagem | Geracao unificada de imagens. |
| `POST /v1/videos/generations` | Video | Geracao unificada de videos. |
| `GET /v1/models` | Listar | Modelos com metadados completos. Filtros: `?pricing=free`, `?capability=vision`. |
| `GET /v1/models/{id}` | Detalhes | Metadados detalhados de um modelo. |
| `GET /v1/capabilities/summary` | Resumo | Quantos gratis, com visao, audio, reasoning, etc. |
| `GET /v1/providers` | Provedores | Metadados globais por provedor. |

---

## Instalacao Rapida

### Windows (Recomendado: Duplo-clique em `start.bat`)

```bash
git clone https://github.com/seu-usuario/wallasapi.git
cd wallasapi
# Duplo-clique em start.bat
```

### Linux / macOS

```bash
git clone https://github.com/seu-usuario/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

Servidor inicia em **http://localhost:8001**

Documentacao interativa: **http://localhost:8001/docs**

---

## Configuracao

Crie um arquivo `.env` com as chaves API dos provedores que deseja usar. **Nao precisa de todas.**

```env
# Provedores gratuitos (recomendados para comecar)
GEMINI_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui
GITHUB_TOKEN=seu_token_aqui

# Provedores pagos (opcionais)
OPENAI_API_KEY=sua_chave_aqui
OPENROUTER_API_KEY=sua_chave_aqui
```

---

## Licenca

Projeto licenciado sob MIT personalizado. Mantenha a atribuicao a **Willen Ponce**.

**Pedido pessoal:** Se usar WallasAPI, envie um email para **wubjak@protonmail.ch** contando que esta usando. Um simples "Ola, estou usando WallasAPI para X, obrigado por construir" ja faz o dia de um desenvolvedor que construiu isso em um notebook de 2018.

Ver arquivo `LICENSE` para o texto completo.

---

## Doacoes: Manter Isso Vivo

Este projeto nao tem patrocinadores. Nao tem investidores de Silicon Valley. Tem um notebook de 2018, um quarto alugado, e codigo que funciona.

**Se WallasAPI te economizou horas de integracao ou ajudou a construir algo legal:**

- **PayPal**: [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi**: [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **Email**: wubjak@protonmail.ch

**Yape / Plin (Peru) — Numero: 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**Carteiras Crypto:**

| Moeda | Endereco |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"Antes de me botarem da casa, para poder tomar cafe da manha, pagar minhas dividas, e dormir pelo menos 4 horas seguidas sem acordar pensando em quanto devo, toda contribuicao conta. Obrigado por usar WallasAPI."* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>Uma API para governar todos.<br>
  Construida da precariedade, com a determinacao de quem nao tem nada a perder.</em>
</p>
