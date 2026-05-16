# test_peru.py
import os
import sys

# Asegurar que el directorio raíz del proyecto está en el path (tests/ está dos niveles bajo la raíz)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wallasAPI.router import AIRouter
from wallasAPI.model_fetcher import update_registry_cache

def test_final():
    print("--- Probando WallasAPI: Consultas de Perú ---")
    update_registry_cache()
    
    router = AIRouter()
    
    preguntas = [
        "¿Qué hora es en Perú actualmente?",
        "¿Cómo está el clima en Arequipa hoy?"
    ]
    
    for p in preguntas:
        print(f"\nPregunta: {p}")
        print("Buscando en tiempo real...")
        
        try:
            respuesta = router.get_completion(
                system_prompt="Eres un asistente local de Perú. Proporciona información precisa basada en los resultados de búsqueda.",
                user_prompt=p,
                web_search=True
            )
            
            print("\n" + "="*50)
            print("RESPUESTA DE WALLASAPI:")
            print("="*50)
            print(respuesta)
            print("="*50)
            
        except Exception as e:
            print(f"\n[ERROR]: {e}")

if __name__ == "__main__":
    test_final()
