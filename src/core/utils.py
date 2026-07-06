import re
import csv
import json
import os
import logging

logger = logging.getLogger("scrapic")


def setup_logging(level: int = logging.INFO):
    """Configura el logger global de Scrapic. Llamar una vez al inicio de la aplicación."""
    log = logging.getLogger("scrapic")
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
        log.addHandler(handler)
    log.setLevel(level)

class FileUtils:
    """Utilidades para sanitizar nombres, crear directorios y validar la integridad interna de archivos descargados."""
    
    @staticmethod
    def make_concept_dir(base: str, concept: str) -> str:
        """Crea y retorna el directorio destino para un concepto. Centraliza la lógica compartida entre scrapers."""
        concept_dir = os.path.join(base, concept.replace(" ", "_"))
        os.makedirs(concept_dir, exist_ok=True)
        return concept_dir

    @staticmethod
    def clean_filename(filename: str) -> str:
        """Limpia la basura de la web: espacios, caracteres especiales, y codificación URL."""
        import urllib.parse
        clean = urllib.parse.unquote(filename)
        # Solo permite alfanuméricos, puntos, guiones y guiones bajos
        clean = re.sub(r'[^a-zA-Z0-9.\-_]', '_', clean)
        # Eliminar múltiples guiones bajos
        clean = re.sub(r'_+', '_', clean)
        return clean.strip('_')

    @staticmethod
    def validate_size(filepath: str, min_size_mb: float) -> bool:
        """Verifica que el tamaño real del archivo en disco sea al menos min_size_mb."""
        if min_size_mb <= 0: return True
        try:
            import os
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if size_mb < min_size_mb:
                logger.debug(f"Tamaño ({size_mb:.2f}MB) menor al mínimo ({min_size_mb}MB).")
                return False
            return True
        except Exception as e:
            logger.debug(f"Error comprobando tamaño de {filepath}: {e}")
            return False

    @staticmethod
    def validate_pdf(filepath: str, min_pages: int) -> bool:
        """Filtro Inteligente: Abre el PDF en memoria y cuenta las páginas."""
        if min_pages <= 0: return True
        try:
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                if num_pages < min_pages:
                    logger.debug(f"PDF inválido: Solo tiene {num_pages} páginas (mínimo {min_pages}).")
                    return False
            return True
        except Exception as e:
            logger.debug(f"Error leyendo PDF {filepath}: {e}")
            return False

    @staticmethod
    def validate_dataset(filepath: str, ext: str, min_rows: int = 10, min_cols: int = 2) -> bool:
        """Filtro Inteligente: Abre el archivo local y verifica si realmente es un dataset válido, o basura."""
        try:
            if ext == '.csv':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if not header or len(header) < min_cols: 
                        logger.debug(f"Dataset inválido: {filepath} tiene menos de {min_cols} columnas.")
                        return False
                    rows = sum(1 for row in reader)
                    if rows < min_rows: 
                        logger.debug(f"Dataset inválido: {filepath} tiene solo {rows} filas (mínimo {min_rows}).")
                        return False
                return True
            
            elif ext == '.json':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) >= min_rows:
                        return True
                    elif isinstance(data, dict) and len(data.keys()) >= min_rows:
                        return True
                    else:
                        logger.debug(f"Dataset JSON inválido: {filepath} no cumple los requisitos de tamaño.")
                        return False
            
            else:
                # Para .xlsx, .md y otros: los damos por buenos (no hay validación interna implementada)
                return True
                
        except Exception as e:
            logger.debug(f"Error parseando dataset {filepath}: {e}")
            return False
