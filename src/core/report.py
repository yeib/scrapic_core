import csv
import os
import threading
from datetime import datetime
import logging

logger = logging.getLogger("scrapic")

class OSINTReporter:
    """Generador de reportes OSINT en formato CSV.
    Registra cada descarga realizada para mantener trazabilidad."""
    
    def __init__(self, report_file: str = "reporte_scrapic.csv"):
        self.report_file = report_file
        self._lock = threading.Lock()
        self._init_csv()
        
    def _init_csv(self):
        """Crea el archivo CSV con sus cabeceras si no existe."""
        if not os.path.exists(self.report_file):
            try:
                with open(self.report_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Fecha_Hora", "Archivo_Local", "URL_Origen", "Mision_Origen", "Tamano_MB"])
            except Exception as e:
                logger.error(f"Error creando reporte CSV: {e}")
                
    def log_download(self, filepath: str, url: str, source: str):
        """Registra una descarga exitosa en el reporte de forma segura (Thread-safe)."""
        try:
            size_mb = 0.0
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with self._lock:
                with open(self.report_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, filepath, url, source, f"{size_mb:.2f}"])
        except Exception as e:
            logger.debug(f"Error guardando en reporte CSV: {e}")
