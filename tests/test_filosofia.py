# test_filosofia.py
import os
import sys

# Asegurar que el directorio raíz del proyecto está en el path (tests/ está dos niveles bajo la raíz)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wallasAPI.router import AIRouter
from wallasAPI.model_fetcher import update_registry_cache

def test_query():
    print("--- Probando WallasAPI ---")
    print("Cargando registro de modelos...")
    update_registry_cache()
    
    router = AIRouter()
    
    pregunta = "¿Podrías explicar brevemente qué es el pensamiento socrático y quiénes eran los peripatéticos?"
    
    print(f"\nPregunta: {pregunta}")
    print("\nGenerando respuesta (usando enrutamiento inteligente)...")
    
    try:
        # Usamos razonamiento para una mejor respuesta filosófica
        respuesta = router.get_completion(
            system_prompt="Eres un experto en filosofía clásica. Responde de forma clara y estructurada.",
            user_prompt=pregunta,
            reasoning=True
        )
        
        print("\n" + "="*50)
        print("RESPUESTA DE WALLASAPI:")
        print("="*50)
        print(respuesta)
        print("="*50)
        
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un fallo en la prueba: {e}")

if __name__ == "__main__":
    test_query()
