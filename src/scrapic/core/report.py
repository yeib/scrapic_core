import os
import logging
from scrapic.core.database import DatabaseManager

logger = logging.getLogger("scrapic")

class OSINTReporter:
    """Generador de reportes OSINT usando SQLite.
    Registra cada descarga realizada para mantener trazabilidad.
    """
    def __init__(self, report_file: str = "scrapic.db"):
        self.report_file = report_file # Mantenemos el atributo por compatibilidad
        self.db = DatabaseManager(db_path=report_file)
        
    def log_download(self, filepath: str, url: str, source: str) -> bool:
        """Registra una descarga y devuelve si se persistió correctamente."""
        try:
            size_mb = 0.0
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            persisted = self.db.log_download(url=url, filepath=filepath, source=source, size_mb=size_mb)
            if not persisted:
                logger.error("No se pudo persistir el reporte de descarga para %s", url)
            return persisted
        except Exception as e:
            logger.error(f"Error guardando en reporte DB: {e}")
            return False
