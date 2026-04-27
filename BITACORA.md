# AI Services: Bitácora Técnica de Implementación
**Fecha: 2026-04-08**

## 🏗️ Evolución Modular
Se ha realizado una transición completa desde un archivo monolítico (`ai_router.py`) a un paquete estructurado `ai_services/`. Esta decisión permite que el motor de IA sea agnóstico al resto del proyecto "Monster VIP".

## 🛠️ Componentes Creados:
1.  **`router.py`**: El núcleo multicapa. Gestiona fallbacks entre 8 proveedores distintos y es consciente de las capacidades de visión de cada modelo.
2.  **`memory.py`**: Gestor de persistencia que evita la pérdida de contexto al saltar entre proveedores gratuitos ("State Handover").
3.  **`config.py`**: Registro central de más de 45 modelos, permitiendo actualizaciones rápidas sin tocar la lógica del router.

## 🚀 Logros Clave:
- **Resiliencia**: Manejo de errores 429 y cuotas agotadas mediante ruteo en cascada.
- **Eficiencia**: Filtrado de modelos por visión cuando se detectan `images`.
- **Portabilidad**: El paquete es 100% independiente y reutilizable.
- **Saneamiento**: Eliminación de emojis y carácteres especiales para compatibilidad total con Windows CMD/PowerShell.
