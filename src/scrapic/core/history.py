import logging
from scrapic.core.database import DatabaseManager

logger = logging.getLogger("scrapic")

class HistoryManager:
    """Gestiona el historial de descargas para evitar archivos repetidos usando SQLite.
    Thread-safe por naturaleza de DatabaseManager.
    """
    def __init__(self, history_file: str = "scrapic.db", save_every: int = 10):
        # history_file se reinterpreta como db_path para mantener compatibilidad
        self.db = DatabaseManager(db_path=history_file)

    def is_downloaded(self, url: str) -> bool:
        """Devuelve True si la URL ya fue descargada previamente."""
        return self.db.is_downloaded(url)

    def mark_as_downloaded(self, url: str) -> bool:
        """Marca una URL como descargada en SQLite y devuelve el estado de persistencia."""
        persisted = self.db.mark_as_downloaded(url)
        if not persisted:
            logger.error("No se pudo persistir en historial la URL %s", url)
        return persisted

    def flush(self):
        """No es necesario con SQLite directo, se mantiene por compatibilidad de API."""
        pass
