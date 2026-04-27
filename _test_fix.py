"""Quick verification of model fixes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_services import MODELS_REGISTRY, update_registry_cache, NON_CHAT_TYPES

update_registry_cache()

print("\n=== CEREBRAS (should have no orpheus/allam) ===")
for m in MODELS_REGISTRY:
    if m["provider"] == "cerebras":
        print(f"  {m['id']}  caps={m['capabilities']}")

print("\n=== COHERE (should only be command-*/aya-*) ===")
for m in MODELS_REGISTRY:
    if m["provider"] == "cohere":
        print(f"  {m['id']}  caps={m['capabilities']}")

print("\n=== GITHUB ===")
for m in MODELS_REGISTRY:
    if m["provider"] == "github":
        print(f"  {m['id']}  caps={m['capabilities']}")

print("\n=== GROQ (no orpheus/allam) ===")
for m in MODELS_REGISTRY:
    if m["provider"] == "groq":
        print(f"  {m['id']}  caps={m['capabilities']}")

# Count
chat = [m for m in MODELS_REGISTRY if not (set(m["capabilities"]) & NON_CHAT_TYPES)]
print(f"\nTotal: {len(MODELS_REGISTRY)}, Chat: {len(chat)}")
