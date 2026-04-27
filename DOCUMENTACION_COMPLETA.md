# 📘 MANUAL MAESTRO — WallasAPI (The Intelligence Core)

Bienvenido a la documentación oficial de **WallasAPI**. Este sistema es el corazón de inteligencia de **Legalia OS** y el ecosistema **Willaku**. Actúa como un proxy universal que unifica más de 650 modelos de IA en una única interfaz estandarizada y resiliente.

---

## 📑 CONTENIDO
1.  [Visión General](#-visión-general)
2.  [Arquitectura del Sistema](#-arquitectura-del-sistema)
3.  [Capacidades y Funciones Avanzadas](#-capacidades-y-funciones-avanzadas)
4.  [Guía de Integración (IDEs: Cursor, Windsurf, Copilot)](#-guía-de-integración)
5.  [Referencia de la API (Endpoints)](#-referencia-de-la-api)
6.  [Configuración del Entorno (.env)](#-configuración-del-entorno)
7.  [Enrutamiento y Tiers (Lógica de Decisión)](#-enrutamiento-y-tiers)

---

## 🚀 VISIÓN GENERAL
WallasAPI es un **Proxy de IA Multiproveedor** de alto rendimiento. Su objetivo es abstraer la complejidad de las diferentes APIs (Google, NVIDIA, Groq, Anthropic, OpenAI, Ollama) para ofrecer una experiencia fluida tanto a aplicaciones internas como a herramientas externas.

### Diferenciadores Clave:
-   **Independencia de Proveedor**: Cambia de proveedor en milisegundos sin tocar el código del cliente.
-   **Catálogo Dinámico**: Detecta automáticamente nuevos modelos al iniciar (650+ modelos actualmente).
-   **Resiliencia Automática (Fallback)**: Si un proveedor falla, WallasAPI busca el mismo modelo o uno equivalente en otro proveedor instantáneamente.
-   **Shim de Archivos**: Permite enviar documentos (PDF, Docx) incluso a modelos que no tienen visión nativa, procesándolos mediante OCR y "Text Injection".

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### 1. WallasRouter (`router.py`)
Es el motor de ejecución. Sus responsabilidades incluyen:
-   **Normalización**: Traduce formatos OpenAI/Anthropic al formato específico de cada proveedor.
-   **Balanceo de Carga**: Distribuye el tráfico entre proveedores con modelos idénticos.
-   **Control de Cooldown**: Desactiva temporalmente proveedores que devuelven errores (Rate Limit/Overload).

### 2. ModelFetcher (`model_fetcher.py`)
El descubridor de modelos. Escanea:
-   **Nubes**: OpenRouter, Google Vertex, Mistral, NVIDIA NIM, Sambanova.
-   **Local**: Ollama (detecta tus modelos descargados).
-   **Clasificación**: Usa heurística para etiquetar modelos como `VISION`, `CODE`, `REASONING`, `FREE`, etc.

### 3. FileProcessor (`file_utils.py`)
La capa de procesamiento multimodal:
-   Extrae texto de PDFs y archivos de audio.
-   Aplica OCR en cascada: intenta con Gemini (nativo) -> Mistral -> Tesseract/EasyOCR local.

### 4. MemoryManager (`memory.py`)
Gestiona la persistencia:
-   Guarda hilos de conversación en `temp_context/`.
-   Permite sincronizar chats directamente a un Vault de **Obsidian**.

---

## ✨ CAPACIDADES Y FUNCIONES AVANZADAS

En lugar de elegir un modelo específico, puedes usar las 4 Categorías Maestras enviando el header `X-Willaku-Tier`:
-   **`razonamiento`**: Usa modelos de pensamiento profundo (DeepSeek-R1, o1, Gemini Thinking).
-   **`standard`**: Modelos equilibrados y de alta calidad (GPT-4o, Claude 3.5 Sonnet).
-   **`rapido`**: Modelos ultra-rápidos y eficientes (Llama 3.1 8B, Gemini Flash).
-   **`auto`**: Elige la mejor opción según el contexto, priorizando siempre los modelos GRATUITOS.

### 🌐 Web Search Integrado
Envía `X-Willaku-Web-Search: true` y WallasAPI buscará en tiempo real en DuckDuckGo antes de responder, inyectando los resultados como contexto actualizado.

---

## 💻 GUÍA DE INTEGRACIÓN (IDEs)

WallasAPI ha sido optimizado para ser el backend perfecto de **Cursor**, **Windsurf** y **Copilot**.

### Configuración en Cursor / Windsurf:
1.  **Tipo de Proveedor**: Selecciona "OpenAI Compatible".
2.  **Base URL**: `http://localhost:8001/v1`
3.  **API Key**: Usa el valor de `PROXY_API_KEY` de tu `.env` (o deja cualquier texto si está vacío).
4.  **Embeddings**: Configurado automáticamente en el puerto 8001 para que la indexación de código funcione sin fallos.

---

## 📡 REFERENCIA DE LA API

### Chat Completions (OpenAI Style)
`POST /v1/chat/completions`
Formato estándar. Soporta streaming.

### Embeddings (NUEVO)
`POST /v1/embeddings`
Permite generar vectores para búsqueda semántica. WallasAPI redirige a modelos eficientes (NVIDIA o Ollama).

### Anthropic Messages (Claude Style)
`POST /v1/messages`
Ideal para herramientas que prefieren el protocolo de Anthropic.

### OCR & Interpretación
-   `POST /v1/ocr/process`: Extrae texto de imágenes/PDFs.
-   `POST /v1/interpret`: Describe visualmente una imagen codificada en base64.

---

## 🚥 ENRUTAMIENTO Y TIERS

WallasAPI usa una lógica de "Cascada de Fallback":
1.  **Match Exacto**: Intenta el modelo solicitado.
2.  **Redundancia**: Si falla, intenta el mismo modelo en otro proveedor.
3.  **Sustitución**: Si no hay stock, usa un modelo "hermano" de similar capacidad.
4.  **Seguridad**: Nunca enviará una petición que supere los límites conocidos del modelo.

---
**WallasAPI — El Futuro de la Inteligencia Legal Organizada.**
*Desarrollado por ProyectoIG para Legalia OS.*
