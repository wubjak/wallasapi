# Manual Técnico: WallasAPI (The Intelligence Core)
Este módulo es un orquestador de modelos de IA de alto rendimiento, gratuito y multicanal.

## 🗝️ Configuración Necesaria
El módulo espera que las siguientes variables de entorno estén presentes (vía `.env` o sistema):
- `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `SAMBANOVA_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `CEREBRAS_API_KEY`, `COHERE_API_KEY`.

## 📂 Directorio de Memoria
El sistema crea automáticamente la carpeta `temp_context/` dentro de este paquete. Aquí se guardan los threads de conversación por su `thread_id`.

## 🚀 Uso Rápido (Reutilización)
Para integrar este módulo en cualquier proyecto:

```python
from wallasAPI import WallasClient as WallasAPI

router = AIRouter()
# Si hay imágenes, enviarlas como lista de base64
resultado = router.get_completion(
    system_prompt="Tu prompt de sistema",
    user_prompt="Tu pregunta aquí",
    thread_id="usuario_unico_123"
)
print(resultado)
```

## 📋 Prioridad de Modelos (Reserva Deep)
El sistema consultará en este orden:
1. **Calidad Premium**: GPT-4o, Gemini 2.0.
2. **Visión Especializada**: Pixtral-12B, Llama-4 Maverick.
3. **Razonamiento**: DeepSeek-R1 (múltiples proveedores).
4. **Resistencia (Fallback)**: Groq, Cerebras, Mistral Large.
5. **Legión OpenRouter**: Flota masiva de modelos gratuitos.
