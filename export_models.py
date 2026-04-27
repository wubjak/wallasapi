# -*- coding: utf-8 -*-
import os
import sys
import datetime
from fpdf import FPDF

# Asegurar que el directorio raíz está en el path para importar ai_services
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_services.config import (
    MODELS_REGISTRY, FREE, VISION, REASONING, MOE, AUDIO, CODE, FILE, FILE_SHIM, TTS
)
from ai_services.model_fetcher import update_registry_cache

class ModelPDF(FPDF):
    def header(self):
        # Logo o Título
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(0, 210, 255) # Cyan premium
        self.cell(0, 10, 'GRAVEDAD AI - CATALOGO DE MODELOS', 0, 1, 'C')
        self.ln(5)
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 5, f'Generado el: {date_str}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def export_to_pdf():
    print("Cargando registro de modelos...")
    update_registry_cache()
    
    if not MODELS_REGISTRY:
        print("No hay modelos en el registro para exportar.")
        return

    pdf = ModelPDF()
    # Usar fuente Unicode para soportar emojis si es posible, 
    # pero como usamos Helvetica (standard), usaremos texto descriptivo con simbolos ASCII seguros
    # o simplemente los nombres de las categorias de Gravedad.
    pdf.add_page()
    
    # Agrupar por proveedor
    providers = {}
    for m in MODELS_REGISTRY:
        p = m.get('provider', 'Desconocido').upper()
        if p not in providers:
            providers[p] = []
        providers[p].append(m)

    for p_name in sorted(providers.keys()):
        # Título del Proveedor
        pdf.set_fill_color(20, 23, 31) # Fondo oscuro
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, f'  PROVEEDOR: {p_name}', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        # Tabla de Modelos
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        
        # Cabecera de tabla optimizada
        pdf.cell(80, 8, ' ID del Modelo', 1, 0, 'L', fill=True)
        pdf.cell(25, 8, ' Categoria', 1, 0, 'C', fill=True)
        pdf.cell(85, 8, ' Capacidades Detectadas', 1, 1, 'C', fill=True)
        
        pdf.set_font('helvetica', '', 9)
        for m in providers[p_name]:
            caps = m.get('capabilities', [])
            is_free = FREE in caps
            
            # Recolectar etiquetas de capacidades (estilo Gravedad)
            tags = []
            if VISION in caps: tags.append("Vision")
            if AUDIO in caps: tags.append("Audio")
            if REASONING in caps: tags.append("Razonamiento")
            if MOE in caps: tags.append("MoE")
            if CODE in caps: tags.append("Codigo")
            if FILE in caps or FILE_SHIM in caps: tags.append("Archivos")
            if TTS in caps: tags.append("Voz")
            
            caps_str = " + ".join(tags) if tags else "Texto"
            
            # ID (truncado si es muy largo)
            model_id = m["id"]
            if len(model_id) > 40: model_id = model_id[:37] + "..."
            pdf.cell(80, 7, f' {model_id}', 1, 0, 'L')
            
            # Categoria (Gratis/Pago)
            if is_free:
                pdf.set_text_color(0, 150, 0) # Verde
                pdf.cell(25, 7, 'GRATIS', 1, 0, 'C')
            else:
                pdf.set_text_color(200, 0, 0) # Rojo
                pdf.cell(25, 7, 'PREMIUM', 1, 0, 'C')
            
            pdf.set_text_color(0, 0, 0)
            
            # Capacidades
            pdf.set_font('helvetica', 'I', 8)
            pdf.cell(85, 7, f' {caps_str}', 1, 1, 'L')
            pdf.set_font('helvetica', '', 9)
            
        pdf.ln(5)

    output_path = os.path.join(project_root, "Lista_Modelos_Gravedad.pdf")
    pdf.output(output_path)
    print(f"Catalogo exportado exitosamente: {output_path}")

if __name__ == "__main__":
    export_to_pdf()
