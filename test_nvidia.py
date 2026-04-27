import os
import asyncio
from dotenv import load_dotenv
load_dotenv('ai_services/.env')

from ai_services.model_fetcher import update_registry_cache
from ai_services.router import AIRouter

def test_nvidia():
    print("--- Actualizando Registro ---")
    models = update_registry_cache()
    nv_models = [m for m in models if m['provider'] == 'nvidia']
    print(f"Total modelos: {len(models)}")
    print(f"Modelos NVIDIA: {len(nv_models)}")
    
    if not nv_models:
        print("ERROR: No se encontraron modelos de NVIDIA.")
        return

    # List some models
    for m in nv_models[:20]:
        print(f"  - {m['id']} (Caps: {m['capabilities']})")

    print("\n--- Probando Inferencia (NVIDIA) ---")
    router = AIRouter()
    # Try a known good model or the first one in the list
    test_model = "nvidia/llama-3.1-405b-instruct" if any("llama-3.1-405b" in m['id'] for m in nv_models) else nv_models[0]['id']
    print(f"Probando con: {test_model}")
    
    try:
        response = router.get_completion(
            system_prompt="Eres un asistente útil.",
            user_prompt="Hola, ¿quién eres y qué modelo estás usando?",
            preferred_model=test_model
        )
        print(f"Respuesta: {response}")
    except Exception as e:
        print(f"Error en inferencia: {e}")

if __name__ == "__main__":
    test_nvidia()
