# test_search.py
import os
import sys

# Asegurar que el directorio raíz del proyecto está en el path (tests/ está dos niveles bajo la raíz)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wallasAPI.router import AIRouter

def test_web_search():
    print("--- Probando WallasAPI con Web Search ---")
    from wallasAPI.model_fetcher import update_registry_cache
    update_registry_cache()
    
    router = AIRouter()
    
    # Pregunta sobre algo muy reciente o que requiera datos externos
    pregunta = "precio bitcoin hoy"
    
    print(f"\nPregunta: {pregunta}")
    print("\nActivando búsqueda web en tiempo real...")
    
    try:
        # Activamos web_search=True
        respuesta = router.get_completion(
            system_prompt="Eres un analista financiero que usa datos de búsqueda web en tiempo real.",
            user_prompt=pregunta,
            web_search=True
        )
        
        print("\n" + "="*50)
        print("RESPUESTA DE WALLASAPI (CON WEB SEARCH):")
        print("="*50)
        print(respuesta)
        print("="*50)
        
    except Exception as e:
        print(f"\n[ERROR] La búsqueda web falló: {e}")

if __name__ == "__main__":
    test_web_search()
