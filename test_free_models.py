#!/usr/bin/env python3
"""
Prueba completa para detectar TODOS los modelos gratis de cada provider.
Compara la detección actual vs la detección mejorada.
"""
import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "github": {
        "url": "https://models.inference.ai.azure.com/models",
        "env_key": "GITHUB_TOKEN",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "env_key": "GROQ_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "sambanova": {
        "url": "https://api.sambanova.ai/v1/models",
        "env_key": "SAMBANOVA_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/models",
        "env_key": "CEREBRAS_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "nvidia": {
        "url": "https://integrate.api.nvidia.com/v1/models",
        "env_key": "NVIDIA_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "env_key": "MISTRAL_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "env_key": "OPENROUTER_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "cohere": {
        "url": "https://api.cohere.ai/v1/models",
        "env_key": "COHERE_API_KEY",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}"},
    },
    "gemini": {
        "url": None,  # Special handling
        "env_key": "GEMINI_API_KEY",
        "headers_fn": lambda k: {},
    },
}

# Reglas MEJORADAS de detección de gratis
FREE_PATTERNS = {
    # Todos los modelos de estos providers son gratis (con rate limits)
    "github": lambda mid: True,
    "groq": lambda mid: True,
    "sambanova": lambda mid: True,
    "cerebras": lambda mid: True,
    "ollama": lambda mid: True,
    "pollinations": lambda mid: True,
    "huggingface": lambda mid: True,

    # NVIDIA: casi todos son gratis en free tier, excepto algunos específicos
    "nvidia": lambda mid: not any(x in mid.lower() for x in [
        # Modelos que requieren créditos/pago explícito
    ]),

    # Gemini: Flash y Lite son gratis, Pro es "free tier" generoso
    "gemini": lambda mid: any(x in mid.lower() for x in ["flash", "lite", "gemma"]) or "pro" in mid.lower(),

    # OpenRouter: SOLO los que terminan en :free son gratis
    "openrouter": lambda mid: ":free" in mid.lower(),

    # Mistral: La Plateforme es de pago, pero tienen modelos gratis en tiers limitados
    "mistral": lambda mid: any(x in mid.lower() for x in ["pixtral", "mistral-small", "mistral-medium"]),

    # Cohere: Algunos modelos tienen trial gratis
    "cohere": lambda mid: True,  # Todos tienen trial generoso
}

EXCLUDED_PATTERNS = [
    "robotics", "computer-use", "deep-research", "customtools",
    "prompt-guard", "safeguard", "compound",
    "orpheus", "transcribe", "allam",
    "embedding", "embed", "rerank", "tts",
    "sdxl", "flux", "dall-e", "imagen",  # image gen
    "safety", "guard", "parse", "pii", "deplot", "gliner", "ocr",
    "kosmos-2", "fuyu-8b", "iva-", "imaging-",
]


def is_chat_model(mid: str) -> bool:
    """Heurística: ¿es un modelo de chat/completion usable?"""
    m = mid.lower()
    if any(p in m for p in EXCLUDED_PATTERNS):
        return False
    return True


def is_free_enhanced(mid: str, provider: str) -> bool:
    """Nueva detección mejorada de gratis."""
    rule = FREE_PATTERNS.get(provider)
    if rule:
        return rule(mid)
    return False


def is_free_current(mid: str, provider: str) -> bool:
    """Simula la detección ACTUAL del código."""
    free_providers = {"groq", "sambanova", "cerebras", "github", "ollama"}
    if provider in free_providers:
        return True
    if ":free" in mid.lower() or "free" in mid.lower():
        return True
    if provider == "gemini" and any(x in mid.lower() for x in ["flash", "lite", "gemma"]):
        return True
    if provider == "nvidia":
        return True
    return False


async def fetch_models(session: aiohttp.ClientSession, provider: str, config: dict):
    """Obtiene modelos de un provider."""
    api_key = os.getenv(config["env_key"])
    if not api_key:
        return provider, [], "NO_KEY"

    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = []
                    for m in data.get("models", []):
                        m_id = m.get("name", "").replace("models/", "")
                        if "generateContent" in m.get("supportedGenerationMethods", []):
                            models.append(m_id)
                    return provider, models, "OK"
                return provider, [], f"HTTP {resp.status}"
        except Exception as e:
            return provider, [], f"ERROR: {e}"

    url = config["url"]
    headers = config["headers_fn"](api_key)
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                # OpenRouter usa "data" como lista
                if provider == "openrouter":
                    items = data.get("data", [])
                else:
                    items = data.get("data", data) if isinstance(data, dict) else data

                models = []
                for m in items:
                    if isinstance(m, dict):
                        if provider == "github":
                            m_id = m.get("name", m.get("id", ""))
                        else:
                            m_id = m.get("id", "")
                        if m_id:
                            models.append(m_id)
                return provider, models, "OK"
            return provider, [], f"HTTP {resp.status}"
    except Exception as e:
        return provider, [], f"ERROR: {e}"


async def main():
    print("=" * 70)
    print("  PRUEBA COMPLETA: Detección de modelos GRATIS")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_models(session, name, cfg) for name, cfg in PROVIDERS.items()]
        results = await asyncio.gather(*tasks)

    report = {}
    total_current = 0
    total_enhanced = 0
    total_chat = 0

    for provider, models, status in results:
        print(f"\n{'='*70}")
        print(f"Provider: {provider.upper()} | Status: {status}")
        print(f"{'='*70}")

        if status != "OK" or not models:
            print(f"  ⚠️  {status} - Sin modelos")
            continue

        chat_models = [m for m in models if is_chat_model(m)]
        current_free = [m for m in chat_models if is_free_current(m, provider)]
        enhanced_free = [m for m in chat_models if is_free_enhanced(m, provider)]

        # Modelos que el sistema actual NO detecta como gratis pero debería
        missed = [m for m in chat_models if m not in current_free and m in enhanced_free]
        # Modelos que el sistema actual marca gratis pero NO debería
        false_positives = [m for m in chat_models if m in current_free and m not in enhanced_free]

        print(f"  Total modelos: {len(models)}")
        print(f"  Modelos de chat: {len(chat_models)}")
        print(f"  Gratis (detección ACTUAL): {len(current_free)}")
        print(f"  Gratis (detección MEJORADA): {len(enhanced_free)}")

        if missed:
            print(f"\n  ❌ Modelos NO detectados como gratis (pero SÍ lo son):")
            for m in missed[:20]:
                print(f"     - {m}")
            if len(missed) > 20:
                print(f"     ... y {len(missed) - 20} más")

        if false_positives:
            print(f"\n  ⚠️  Falsos positivos (marcados gratis pero NO lo son):")
            for m in false_positives[:10]:
                print(f"     - {m}")

        report[provider] = {
            "total": len(models),
            "chat": len(chat_models),
            "current_free": len(current_free),
            "enhanced_free": len(enhanced_free),
            "missed": missed,
            "false_positives": false_positives,
        }

        total_current += len(current_free)
        total_enhanced += len(enhanced_free)
        total_chat += len(chat_models)

    print(f"\n{'='*70}")
    print("  RESUMEN GLOBAL")
    print(f"{'='*70}")
    print(f"  Total modelos de chat detectados: {total_chat}")
    print(f"  Gratis detectados (actual):       {total_current}")
    print(f"  Gratis detectados (mejorado):    {total_enhanced}")
    print(f"  Modelos gratis perdidos:        {total_enhanced - total_current}")

    # Guardar reporte
    report_path = os.path.join(os.path.dirname(__file__), "free_models_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Reporte guardado en: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
