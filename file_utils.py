# ai_services/file_utils.py
"""
File processing utilities for the AI Router.
Handles text extraction from documents (PDF, text, etc.) for models that
don't support native file uploads (shim mode).
"""
import base64
import io

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

from .logger import log

try:
    import easyocr
    import numpy as np
    from PIL import Image
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

try:
    from mistralai import Mistral
    HAS_MISTRAL = True
except ImportError:
    HAS_MISTRAL = False

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    from google import genai
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False


class OCRProcessor:
    """Handles Optical Character Recognition using various engines."""

    @staticmethod
    def local_ocr(file_bytes: bytes, lang=['es', 'en']) -> str:
        """OCR using EasyOCR (Local)."""
        if not HAS_EASYOCR:
            return "[Error: EasyOCR no instalado. Instala con: pip install easyocr]"
        try:
            reader = easyocr.Reader(lang)
            # EasyOCR works best with numpy arrays or PIL images
            img = Image.open(io.BytesIO(file_bytes))
            img_np = np.array(img)
            results = reader.readtext(img_np, detail=0)
            return "\n".join(results)
        except Exception as e:
            return f"[Error OCR Local: {str(e)}]"

    @staticmethod
    def mistral_ocr(file_bytes: bytes, api_key: str) -> str:
        """OCR using Mistral AI API."""
        if not HAS_MISTRAL:
            raise Exception("SDK de Mistral no instalado")
        try:
            client = Mistral(api_key=api_key)
            import base64
            b64_data = base64.b64encode(file_bytes).decode('utf-8')
            from mistralai.models import ImageURLChunk 
            
            response = client.ocr.process(
                model="mistral-ocr-latest",
                document=ImageURLChunk(image_url=f"data:application/pdf;base64,{b64_data}")
            )
            text = ""
            for i, page in enumerate(response.pages):
                text += f"--- OCR Página {i+1} ---\n{page.markdown}\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Mistral OCR falló: {str(e)}")

    @staticmethod
    def llama_local_ocr(file_bytes: bytes, mime_type: str) -> str:
        """OCR using Llama 3.2 Vision locally via Ollama."""
        if not HAS_OLLAMA:
            raise Exception("Ollama (python SDK) no instalado")
        try:
            # Check if mime_type is PDF, Ollama vision only supports images. 
            # We assume it's converted or only first page if PDF. For true PDF to image, 
            # we need pdf2image, but for simplicity we ask the user to upload images for Llama or we do our best.
            # Here we just pass bytes directly, assuming frontend or user passes images if using Llama vision.
            response = ollama.chat(
                model='llama3.2-vision',
                messages=[{
                    'role': 'user',
                    'content': 'Extrae fielmente todo el texto de esta imagen. Si hay tablas o estructuras, usa markdown.',
                    'images': [file_bytes]
                }]
            )
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Llama Local OCR falló: {str(e)}")

    @staticmethod
    def gemini_ocr(file_bytes: bytes, mime_type: str, api_key: str) -> str:
        """OCR using Gemini Multimodal capabilities."""
        if not HAS_GEMINI_SDK:
            raise Exception("Google GenAI SDK no instalado")
        if not api_key:
            raise Exception("Falta GEMINI_API_KEY")
        try:
            client = genai.Client(api_key=api_key)
            # Use direct bytes upload/generation
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    'Analiza este documento y extrae fielmente todo el texto. Genera un formato limpio.',
                    {'mime_type': mime_type, 'data': file_bytes}
                ]
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini OCR falló: {str(e)}")

    @staticmethod
    def auto_ocr(file_bytes: bytes, mime_type: str, preference: str = "cloud_auto") -> str:
        """Intelligent fallback chain for OCR processing."""
        import os
        
        # Define the fallback chains
        if preference == "local_auto":
            chain = ["llama_local", "easyocr", "gemini", "mistral"]
        elif preference == "cloud_auto":
            chain = ["gemini", "mistral", "llama_local", "easyocr"]
        else:
            # If a specific engine is requested, try it first, then fallback to cloud auto
            chain = [preference, "gemini", "mistral", "llama_local", "easyocr"]

        # Deduplicate while preserving order
        unique_chain = []
        for eng in chain:
            if eng not in unique_chain:
                unique_chain.append(eng)

        errors = []
        for engine in unique_chain:
            try:
                log.info(f"Intentando OCR con motor: {engine}")
                if engine == "easyocr":
                     return OCRProcessor.local_ocr(file_bytes)
                elif engine == "mistral":
                     api_key = os.getenv("MISTRAL_API_KEY")
                     if api_key: return OCRProcessor.mistral_ocr(file_bytes, api_key)
                     else: errors.append("Mistral OCR saltado: Falta API KEY")
                elif engine == "gemini":
                     api_key = os.getenv("GEMINI_API_KEY")
                     if api_key: return OCRProcessor.gemini_ocr(file_bytes, mime_type, api_key)
                     else: errors.append("Gemini OCR saltado: Falta API KEY")
                elif engine == "llama_local":
                     # Solo intentar llama si es una imagen, o dejar fallar si es PDF (Ollama no soporta PDF nativamente)
                     if "pdf" not in mime_type.lower():
                         return OCRProcessor.llama_local_ocr(file_bytes, mime_type)
                     else:
                         errors.append("Llama OCR saltado: No soporta PDFs crudos nativamente")
            except Exception as e:
                log.warning(f"Fallo en motor '{engine}': {e}")
                errors.append(f"{engine}: {str(e)}")
                continue
                
        # If all fail
        return f"[Fallo Total OCR]\nDetalles de la cadena:\n" + "\n".join(errors)


class FileProcessor:
    """Extracts and formats text from uploaded files for context injection."""

    # MIME types we can extract text from
    SUPPORTED_TEXT_MIMES = [
        "text/plain", "text/markdown", "text/csv", "text/html",
        "application/json", "application/xml", "text/xml",
        "application/javascript", "text/css",
    ]
    SUPPORTED_PDF_MIMES = ["application/pdf"]

    @staticmethod
    def can_extract(mime_type: str) -> bool:
        """Check if we can extract text from this MIME type."""
        mime_lower = mime_type.lower()
        if any(m in mime_lower for m in ["text/", "json", "xml", "javascript", "css", "markdown"]):
            return True
        if "pdf" in mime_lower:
            return HAS_PYPDF2
        return False

    @staticmethod
    def extract_text(file_data_b64: str, mime_type: str, ocr_engine: str = None) -> dict:
        """
        Extracts text from a base64-encoded file.
        Returns a dict: {"content": str, "needs_ocr": bool, "status": str}
        """
        try:
            if "," in file_data_b64:
                file_data_b64 = file_data_b64.split(",")[1]

            file_bytes = base64.b64decode(file_data_b64)
            mime_lower = mime_type.lower()

            if "pdf" in mime_lower:
                if not HAS_PYPDF2:
                    return {"content": "[Error: PyPDF2 no instalado]", "needs_ocr": False, "status": "error"}
                
                # First attempt: simple text extraction
                text = FileProcessor._extract_from_pdf(file_bytes)
                
                # If no text found and ocr_engine is provided, run OCR
                if "[PDF sin texto extraíble]" in text:
                    if ocr_engine:
                        log.info(f"Derivando PDF a OCR con preferencia: {ocr_engine}")
                        ocr_text = OCRProcessor.auto_ocr(file_bytes, mime_type, ocr_engine)
                        if "[Fallo Total OCR]" in ocr_text:
                            return {"content": ocr_text, "needs_ocr": True, "status": "ocr_failed"}
                        return {"content": ocr_text, "needs_ocr": False, "status": "ocr_success"}
                    else:
                        return {"content": text, "needs_ocr": True, "status": "scanned_pdf"}
                
                return {"content": text, "needs_ocr": False, "status": "success"}

            elif any(m in mime_lower for m in ["text/", "json", "xml", "javascript", "css", "markdown"]):
                return {"content": file_bytes.decode("utf-8", errors="ignore"), "needs_ocr": False, "status": "success"}
            elif any(m in mime_lower for m in ["image/jpeg", "image/png"]):
                if ocr_engine:
                    ocr_text = OCRProcessor.auto_ocr(file_bytes, mime_type, ocr_engine)
                    return {"content": ocr_text, "needs_ocr": False, "status": "ocr_success"}
                return {"content": "[Imagen]", "needs_ocr": True, "status": "image_ocr_available"}
            else:
                return {"content": f"[Formato '{mime_type}' no soportado]", "needs_ocr": False, "status": "unsupported"}
        except Exception as e:
            log.error(f"Error procesando archivo: {e}")
            return {"content": f"[Error: {str(e)}]", "needs_ocr": False, "status": "error"}

    @staticmethod
    def _extract_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Página {i + 1} ---\n{page_text}\n"
            return text.strip() if text.strip() else "[PDF sin texto extraíble (posiblemente es una imagen escaneada)]"
        except Exception as e:
            return f"[Error extrayendo PDF: {str(e)}]"

    @staticmethod
    def format_as_context(files: list, notify_shim: bool = True) -> tuple:
        """
        Takes a list of file dicts {data: str, mime_type: str, name: str}
        and returns a tuple: (context_string, shim_notice_string).
        
        - context_string: The extracted text formatted for injection into the prompt.
        - shim_notice: A user-facing message indicating files were converted to text.
        """
        if not files:
            return "", ""

        context_parts = []
        file_names = []

        for i, f in enumerate(files, 1):
            name = f.get("name", f"Documento_{i}")
            mime = f.get("mime_type", "application/octet-stream")
            file_names.append(name)

            if "extracted_text" in f and f["extracted_text"]:
                # Use the frontend-provided text directly
                context_parts.append(f"📄 ARCHIVO [{name}] (tipo: {mime}):\n{f['extracted_text']}")
            elif FileProcessor.can_extract(mime):
                res = FileProcessor.extract_text(f["data"], mime)
                content = res["content"]
                if res["needs_ocr"]:
                    context_parts.append(f"📄 ARCHIVO [{name}] (tipo: {mime}):\n[AVISO: Este archivo parece ser una imagen o escaneado. Utiliza la herramienta de OCR si es necesario.]")
                else:
                    context_parts.append(f"📄 ARCHIVO [{name}] (tipo: {mime}):\n{content}")
            else:
                context_parts.append(f"📄 ARCHIVO [{name}]: [Formato {mime} no soportado para extracción de texto]")

        context_str = "\n--- DOCUMENTOS ADJUNTOS (convertidos a texto) ---\n"
        context_str += "\n---\n".join(context_parts)
        context_str += "\n--- FIN DE DOCUMENTOS ---\n"

        shim_notice = ""
        if notify_shim:
            shim_notice = f"⚠️ El modelo no soporta archivos nativamente. Se convirtieron a texto: {', '.join(file_names)}"

        return context_str, shim_notice
