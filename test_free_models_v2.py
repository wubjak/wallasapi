#!/usr/bin/env python3
"""
Prueba rápida para validar que las correcciones de _add_free_flag funcionan.
"""
import os
import sys
import json

# Add parent directory so 'wallasAPI' package resolves
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wallasAPI.model_fetcher import _add_free_flag, _determine_capabilities
from wallasAPI.config import FREE

def test_free_flag(model_id: str, provider: str, expected_free: bool):
    caps = []
    _add_free_flag(caps, model_id, provider)
    is_free = FREE in caps
    status = "✅" if is_free == expected_free else "❌"
    print(f"  {status} {provider}/{model_id} -> free={is_free} (expected={expected_free})")
    return is_free == expected_free

print("=" * 70)
print("Validación de _add_free_flag corregido")
print("=" * 70)

all_passed = True

# Mistral
print("\n--- Mistral ---")
for m in ["mistral-small-2506", "mistral-medium-2505", "pixtral-large-latest"]:
    all_passed &= test_free_flag(m, "mistral", True)
for m in ["mistral-large-latest", "codestral-latest"]:
    all_passed &= test_free_flag(m, "mistral", False)

# Gemini
print("\n--- Gemini ---")
for m in ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-3-pro-preview"]:
    all_passed &= test_free_flag(m, "gemini", True)

# OpenRouter
print("\n--- OpenRouter ---")
for m in ["meta-llama/llama-3.1-8b-instruct:free"]:
    all_passed &= test_free_flag(m, "openrouter", True)
for m in ["anthropic/claude-3-5-sonnet", "openai/gpt-4o"]:
    all_passed &= test_free_flag(m, "openrouter", False)

# NVIDIA
print("\n--- NVIDIA ---")
for m in ["nvidia/llama-3.1-nemotron-70b-instruct", "nvidia/cosmos-nemotron-34b"]:
    all_passed &= test_free_flag(m, "nvidia", True)

# HuggingFace
print("\n--- HuggingFace ---")
for m in ["meta-llama/Meta-Llama-3-8B-Instruct"]:
    all_passed &= test_free_flag(m, "huggingface", True)

# Cohere
print("\n--- Cohere ---")
for m in ["command-a", "command-r"]:
    all_passed &= test_free_flag(m, "cohere", True)

# GitHub, Groq, SambaNova, Cerebras
print("\n--- Fully free providers ---")
for provider in ["github", "groq", "sambanova", "cerebras", "ollama", "pollinations"]:
    all_passed &= test_free_flag("any-model", provider, True)

print("\n" + "=" * 70)
if all_passed:
    print("✅ TODAS las pruebas pasaron. Las correcciones están correctas.")
else:
    print("❌ Algunas pruebas fallaron. Revisa los errores arriba.")
print("=" * 70)
