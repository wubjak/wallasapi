# 📓 Bitácora Técnica — WallasAPI

Registro cronológico de hitos. Entradas más recientes arriba.

---

## 📅 2026-04-26 — WallasAPI v3.0

**Evento:** Nacimiento de **WallasAPI v3.0** como núcleo independiente.

### Cambios principales
- **Independencia de proyectos:** se crea la carpeta `wallasAPI/` como núcleo separado de `ai_services/` para permitir evolución agresiva.
- **Optimización de puerto:** cambio del puerto base de 8000 a **8001**.
- **Compatibilidad con IDEs:**
  - Implementación del endpoint `/v1/embeddings` para permitir indexación local en Cursor y Windsurf.
  - Mejora del endpoint `/v1/models` para cumplir con los estándares de seguridad de agentes autónomos.
  - Soporte para modelos "legacy" vía `/v1/completions`.
- **Aliases de modelos:** mapeo automático de versiones específicas (ej. `gpt-4o-2024-08-06`) a los alias del router.
- **Rebranding:** actualización de toda la identidad visual en consola y documentación.

### Estado del sistema
- **Motor:** WallasRouter v3.1.
- **Modelos disponibles:** 650+.
- **Puerto:** 8001 (HTTP).
- **Clientes actualizados:** OpenClaude (Legalia OS).

*Documentado por Antigravity AI.*

---

## 📅 2026-04-08 — AI Services: Bitácora Técnica de Implementación

### 🏗️ Evolución modular
Transición completa desde un archivo monolítico (`ai_router.py`) a un paquete estructurado `ai_services/`. Esta decisión permite que el motor de IA sea agnóstico al resto del proyecto "Monster VIP".

### 🛠️ Componentes creados
1.  **`router.py`** — el núcleo multicapa. Gestiona fallbacks entre 8 proveedores distintos y es consciente de las capacidades de visión de cada modelo.
2.  **`memory.py`** — gestor de persistencia que evita la pérdida de contexto al saltar entre proveedores gratuitos ("State Handover").
3.  **`config.py`** — registro central de más de 45 modelos, permitiendo actualizaciones rápidas sin tocar la lógica del router.

### 🚀 Logros clave
- **Resiliencia:** manejo de errores 429 y cuotas agotadas mediante ruteo en cascada.
- **Eficiencia:** filtrado de modelos por visión cuando se detectan `images`.
- **Portabilidad:** el paquete es 100% independiente y reutilizable.
- **Saneamiento:** eliminación de emojis y caracteres especiales para compatibilidad total con Windows CMD/PowerShell.
