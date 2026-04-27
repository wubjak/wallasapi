# 📓 BITÁCORA DE EVOLUCIÓN — WallasAPI

### 📅 26 de Abril, 2026
**Evento:** Nacimiento de **WallasAPI v3.0**.

#### Cambios Principales:
-   **Independencia de Proyectos**: Se crea la carpeta `wallasAPI/` como el núcleo de **WallasAPI**, separado de `ai_services/` para permitir una evolución agresiva.
-   **Optimización de Puerto**: Cambio del puerto base de 8000 a **8001**.
-   **Compatibilidad con IDEs**:
    -   Implementación del endpoint `/v1/embeddings` para permitir indexación local en Cursor y Windsurf.
    -   Mejora del endpoint `/v1/models` para cumplir con los estándares de seguridad de agentes autónomos.
    -   Soporte para modelos "legacy" vía `/v1/completions`.
-   **Aliases de Modelos**: Mapeo automático de versiones específicas de modelos (ej. `gpt-4o-2024-08-06`) a los alias del router.
-   **Rebranding**: Actualización de toda la identidad visual en consola y documentación.

#### Estado del Sistema:
-   **Motor**: WallasRouter v3.1.
-   **Modelos Disponibles**: 650+.
-   **Puerto**: 8001 (HTTP).
-   **Clientes Actualizados**: OpenClaude (Legalia OS).

---
*Documentado por Antigravity AI.*
