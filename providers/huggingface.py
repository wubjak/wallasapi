# ai_services/providers/huggingface.py
"""
Hugging Face Inference API Provider.
Leverages the official huggingface_hub Python library to execute models for chat,
vision, translation, and other text-based tasks.
"""
import os
import time
from ...ai_services.logger import log

try:
    from huggingface_hub import InferenceClient
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False

from .base import BaseProvider

class HuggingFaceProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        if HAS_HUGGINGFACE and self.api_key:
            self.client = InferenceClient(api_key=self.api_key)
        else:
            self.client = None

    def initialize(self):
        """Validate that the token is present and the library is installed."""
        if not HAS_HUGGINGFACE:
            raise RuntimeError("La librería 'huggingface_hub' no está instalada. Ejecuta: pip install huggingface_hub")
        if not self.api_key:
            raise RuntimeError("Falta HUGGINGFACE_API_KEY en variables de entorno")
        
        # Test basic connection with a fast model
        try:
            self.client.chat_completion(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            log.info("HuggingFace Inference API initializada correctamente.")
        except Exception as e:
            log.warning(f"Error inicializando HuggingFace: {e}")

    def generate_completion(self, model: str, messages: list, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate a complete text response."""
        if not self.client:
            raise RuntimeError("HuggingFace provider no está inicializado (falta token o librería)")
        
        try:
            # We don't map specific vision images here unless required since HF handles image URLs in the new syntax if the model supports it.
            # Convert system message to user message if model doesn't support system persona well, but most modern HF models do.
            response = self.client.chat_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            log.error(f"HuggingFace completion error: {e}")
            raise Exception(f"HuggingFace API Error: {str(e)}")

    def generate_stream(self, model: str, messages: list, temperature: float = 0.7, max_tokens: int = 1024, **kwargs):
        """Generate a streaming text response."""
        if not self.client:
            raise RuntimeError("HuggingFace provider no está inicializado")
            
        try:
            response_stream = self.client.chat_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            for chunk in response_stream:
                if getattr(chunk.choices[0].delta, 'content', None):
                    yield chunk.choices[0].delta.content
        except Exception as e:
            log.error(f"HuggingFace streaming error: {e}")
            yield f"\n[Error de HuggingFace API: {str(e)}]"
