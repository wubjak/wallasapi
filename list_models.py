import requests
import json
from rich.console import Console
from rich.table import Table
from rich import box

def list_ai_models():
    console = Console()
    url = "http://localhost:8000/v1/models"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get("data", [])
        
        if not models:
            console.print("[yellow]⚠️ No se encontraron modelos en el registro.[/yellow]")
            return

        table = Table(title="🤖 Modelos Disponibles en Gravedad AI", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("ID del Modelo", style="cyan", no_wrap=True)
        table.add_column("Proveedor", style="green")
        table.add_column("Capacidades", style="yellow")
        table.add_column("Descripción", style="white")

        for m in models:
            caps = m.get("capabilities", [])
            # Filtrar capacidades para que no se vea "excluded"
            if "excluded" in caps: continue
            
            # Formatear capacidades con emojis
            cap_emojis = []
            if "text" in caps: cap_emojis.append("💬")
            if "vision" in caps: cap_emojis.append("👁️")
            if "audio" in caps: cap_emojis.append("🎧")
            if "reasoning" in caps: cap_emojis.append("🧠")
            if "free" in caps: cap_emojis.append("🆓")
            if "code" in caps: cap_emojis.append("💻")
            if "file" in caps or "file_shim" in caps: cap_emojis.append("📁")
            
            table.add_row(
                m.get("id", "N/A"),
                str(m.get("provider", "desconocido")).capitalize(),
                " ".join(cap_emojis),
                m.get("desc", "-")
            )

        console.print(table)
        console.print(f"\n[bold green]Total:[/bold green] {len(models)} modelos detectados.")
        console.print("\n[dim]Usa estos IDs en tu configuración de OpenClaude.[/dim]")

    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ Error:[/bold red] No se pudo conectar con ai_services. ¿Está el proxy encendido en el puerto 8000?")
    except Exception as e:
        console.print(f"[bold red]❌ Error inesperado:[/bold red] {e}")

if __name__ == "__main__":
    list_ai_models()
