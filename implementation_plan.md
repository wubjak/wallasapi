# Implementación de AI_SERVICES como API Service (FastAPI)

Este plan detalla la transformación del paquete `ai_services` de un módulo interno a un servicio API robusto y profesional, compatible con el estándar de OpenAI, permitiendo su conexión con IDEs y herramientas externas.

## 🛠️ Análisis del Estado Actual (Review Extenso)

El paquete `ai_services` se compone de los siguientes módulos clave:

### 1. `router.py` (La Orquesta)
Es el componente más crítico. Maneja la lógica de reintento entre proveedores.
- **Flujos**: Soporta `get_completion` (sincrónico) y `stream_completion` (generador).
- **Proceso de Decisión**: Clasifica modelos por capacidades (vision, audio, etc.) y filtra según lo que el usuario envía. Si el modelo preferido falla (ej. 429 Rate Limit), tiene la capacidad de buscar el siguiente modelo compatible en la lista.
- **Soporte de Razonamiento**: Extrae `reasoning_content` de modelos tipo DeepSeek o el campo `thought` de Gemini 2.0.

### 2. `model_fetcher.py` (La Inteligencia Dinámica)
Mantiene el sistema actualizado sin necesidad de cambios manuales en el código.
- **Detección Automática**: Al iniciar, barre las APIs de Groq, GitHub, Gemini, etc.
- **Heurísticas de Capacidades**: Asigna etiquetas como `vision`, `reasoning`, `free` basándose en el nombre del modelo.
- **Ollama Cloud Proxy**: Facilita la transición entre modelos locales y modelos experimentales en la nube.

### 3. `memory.py` (La Memoria de Trabajo)
Gestiona la persistencia de conversaciones.
- **Aislamiento**: Usa JSONs individuales por `thread_id`.
- **Ventana de Contexto**: Mantiene los últimos 20 mensajes (personalizable) para optimizar el uso de tokens en modelos gratuitos.

### 4. `file_utils.py` y `search_tool.py` (Enriquecimiento)
- **Extracción Inteligente**: Convierte PDFs y archivos de texto en prompts inyectables.
- **DuckDuckGo Search**: Permite que modelos locales (Ollama) tengan acceso a información en tiempo real.

---

## 🎯 Objetivo de la Transformación
Crear un servidor `server_api.py` que exponga los endpoints `/v1/chat/completions` y `/v1/models`.

### Requisitos Técnicos:
1.  **Compatibilidad Total con OpenAI**: Para que herramientas como **OpenClaw** o **ClaudeCoe** crean que están hablando con OpenAI directamente.
2.  **Streaming Proxy**: El servidor debe ser capaz de retransmitir el flujo de tokens desde el `AIRouter` al cliente en tiempo real.
3.  **Gestión de Threads automática**: Si el cliente no envía un `thread_id`, generar uno o manejar sesiones vía headers.

---

## 🚀 Propuesta de Cambios

### [ai_services]

#### [NEW] [api_server.py](file:///d:/ProyectoIG/gravedad/ai_services/api_server.py)
Creación de un servidor FastAPI con los siguientes componentes:
- **Endpoint POST `/v1/chat/completions`**: Mapeará los campos `model`, `messages`, `stream`, etc., a las funciones del `AIRouter`.
- **Endpoint GET `/v1/models`**: Listará los modelos disponibles recolectados por `model_fetcher`.
- **Manejo de Streaming**: Uso de `StreamingResponse` para enviar eventos de tipo `text/event-stream`.

#### [MODIFY] [router.py](file:///d:/ProyectoIG/gravedad/ai_services/router.py)
- Ajustar pequeños detalles para facilitar la integración con el servidor web (ej. manejo de errores más específico).

---

## 📅 Pasos de Implementación

1.  **Investigación de Headers**: Verificar qué headers específicos envían herramientas como OpenClaw para asegurar compatibilidad.
2.  **Creación del Servidor Base**: Implementar FastAPI y definir los modelos de datos de Pydantic para OpenAI.
3.  **Lógica de Enrutamiento**: Conectar el `/v1/chat/completions` con `router.stream_completion`.
4.  **Pruebas con Clientes Reales**: Usar `curl` y luego algún plugin de VSCode para validar la conexión.

---

## ❓ Preguntas Abiertas
- ¿Deseas que el servidor requiera una API Key personalizada para seguridad?
- ¿Deberíamos implementar un sistema de balanceo de carga entre múltiples keys del mismo proveedor (ej. tener 3 keys de Groq y rotarlas)?
- ¿Qué herramienta externa es la prioridad para probar primero (ej. OpenClaw)?

---

## 🧪 Plan de Verificación

### Pruebas Automatizadas
- Ejecutar `pytest` sobre los endpoints de la API (si se habilitan).
- Probar el flujo de streaming con un script de Python cliente.

### Verificación Manual
- Configurar OpenClaw con el `base_url` del nuevo servicio y verificar que puede listar modelos y chatear.
