import os
import logging
from src.core.database import DatabaseManager

logger = logging.getLogger("scrapic")

class OSINTReporter:
    """Generador de reportes OSINT usando SQLite.
    Registra cada descarga realizada para mantener trazabilidad.
    """
    def __init__(self, report_file: str = "scrapic.db"):
        self.report_file = report_file # Mantenemos el atributo por compatibilidad
        self.db = DatabaseManager(db_path=report_file)
        
    def log_download(self, filepath: str, url: str, source: str):
        """Registra una descarga exitosa en la BD de forma segura (Thread-safe)."""
        try:
            size_mb = 0.0
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            self.db.log_download(url=url, filepath=filepath, source=source, size_mb=size_mb)
        except Exception as e:
            logger.debug(f"Error guardando en reporte DB: {e}")
