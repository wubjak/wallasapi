# 🤖 AI Services: Universal Multi-Provider AI Router
**Arquitectura de Vanguardia para el Enrutamiento Inteligente de Modelos de Lenguaje**

Este módulo representa el núcleo de procesamiento de inteligencia artificial del ecosistema. Diseñado como un proxy robusto y flexible, permite la unificación de múltiples proveedores de LLMs bajo una única interfaz coherente, optimizando el rendimiento, la disponibilidad y los costos.

---

## 🌟 Capacidades Estratégicas

El **AI Router** no es solo un puente de comunicación; es un orquestador inteligente que gestiona:

*   **Ruteo Dinámico**: Selección automática del mejor modelo basado en capacidades específicas (Texto, Visión, Audio, Razonamiento).
*   **Gestión de Disponibilidad (Auto-Fallback)**: Sistema resiliente que, ante fallos de cuota o caídas de servicio (429, 500), conmuta instantáneamente al siguiente mejor proveedor disponible.
*   **Ecosistema Masivo**: Acceso a **más de 500 modelos** de los principales proveedores del mercado.
*   **Optimización de Costos**: Priorización inteligente de **96+ modelos gratuitos**, permitiendo procesar peticiones complejas (modelos de 120B+ parámetros) sin incurrir en costos operativos.
*   **Soporte Multimodal Nativo**:
    -   **Visión**: Procesamiento avanzado de imágenes.
    -   **Audio**: Integración con flujos de audio nativos y transcripción.
    -   **Documentos (File Shim)**: Tecnología propia que permite inyectar contexto de archivos complejos en modelos que no los soportan de forma nativa.

---

## 🔌 Interfaz de API (Compatibilidad Universal)

El módulo expone un servidor **FastAPI** que actúa como un proxy compatible con los estándares de la industria, permitiendo la integración inmediata con herramientas como VS Code, Claude Code y otros agentes autónomos.

### Endpoints Principales

| Ruta | Método | Estándar | Descripción |
| :--- | :--- | :--- | :--- |
| `/v1/models` | `GET` | OpenAI | Listado dinámico de todos los modelos activos y sus capacidades. |
| `/v1/chat/completions` | `POST` | OpenAI | Punto de entrada para chat (soporta streaming y razonamiento). |
| `/v1/messages` | `POST` | Anthropic | Compatibilidad total con el formato de Claude y herramientas Anthropic. |
| `/v1/ocr/process` | `POST` | Interno | Extracción de texto de documentos y PDFs complejos. |
| `/v1/obsidian/sync` | `POST` | Interno | Sincronización directa de conversaciones con bóvedas de Obsidian. |

---

## 🛠 Estructura del Sistema

```text
ai_services/
├── api_server.py      # Servidor FastAPI y gestión de endpoints.
├── router.py          # Cerebro del sistema: lógica de ruteo y fallback.
├── model_fetcher.py   # Descubrimiento dinámico de modelos en tiempo real.
├── memory.py          # Gestión de hilos y persistencia de contexto.
├── file_utils.py      # Procesamiento de archivos y lógica de "File Shim".
├── config.py          # Configuración maestra de proveedores y prioridades.
└── logger.py          # Registro centralizado de eventos y errores.
```

---

## 🚀 Configuración y Despliegue

### Requisitos Previos
*   Python 3.10 o superior.
*   Dependencias listadas en `requirements.txt`.

### Instalación
```bash
# Instalación de dependencias del núcleo
pip install -r ai_services/requirements.txt
```

### Inicio del Servidor
```bash
# Ejecución del proxy en modo desarrollo
python start_proxy.py
```

### Variables de Entorno (.env)
Configura tus credenciales en el archivo `.env` del directorio raíz o dentro de `ai_services/`:
- `GITHUB_TOKEN`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.
- `PROXY_API_KEY` (Opcional): Para asegurar el proxy en entornos públicos.

---

## 🛡 Seguridad y Resiliencia
El sistema opera en dos modos:
1.  **Modo Abierto (Local)**: Ideal para flujos de trabajo internos sin necesidad de autenticación adicional.
2.  **Modo Protegido (VPS)**: Requiere un `Bearer Token` configurado vía `PROXY_API_KEY` para todas las peticiones externas.

---

## ✍️ Autoría
Desarrollado con precisión técnica por **Willen Ponce Ramal**.
Hecho con pasión desde **Arequipa, Perú**.

---
*Optimizado para flujos de trabajo de inteligencia artificial de alto rendimiento.*
