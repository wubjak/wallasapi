# start_proxy.py
"""
Alternative Python-based launcher for the AI Services Proxy.
Can be used instead of the .bat file, especially for cross-platform use.
"""
import sys
import os

def main():
    # Asegurar que la raíz de d:\ProyectoIG esté en PYTHONPATH para encontrar el paquete ai_services
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    print("=" * 48)
    print("  WallasAPI — El Enrutador de IA Definitivo")
    print("  Powered by ProyectoIG")
    print("=" * 48)
    print()
    print("  Endpoints:")
    print("    OpenAI:    http://localhost:8001/v1/chat/completions")
    print("    Anthropic: http://localhost:8001/v1/messages")
    print("    Models:    http://localhost:8001/v1/models")
    print("    Health:    http://localhost:8001/health")
    print()
    print("  Presiona Ctrl+C para detener.\n")

    try:
        import uvicorn
        uvicorn.run(
            "wallasAPI.api_server:app",
            host="0.0.0.0",
            port=8001,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n[INFO] Servidor detenido.")
    except ImportError:
        print("[ERROR] uvicorn no está instalado. Ejecuta: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
