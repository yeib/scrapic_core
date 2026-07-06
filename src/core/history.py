import os
import json
import logging
import threading

logger = logging.getLogger("scrapic")

class HistoryManager:
    """Gestiona el historial de descargas para evitar archivos repetidos.
    Thread-safe: protegido con lock para escrituras concurrentes desde ThreadPoolExecutor.
    Optimizado: guarda a disco en batch cada `save_every` marcas, no en cada URL individual.
    """
    def __init__(self, history_file: str = "scrapic_history.json", save_every: int = 10):
        self.history_file = history_file
        self.save_every = save_every
        self._lock = threading.Lock()
        self._pending_saves = 0
        self.downloaded_urls = self._load_history()

    def _load_history(self) -> set:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data)
            except Exception as e:
                logger.warning(f"No se pudo cargar el historial: {e}")
        return set()

    def _save_history(self):
        """Escritura atómica: guarda a archivo temporal y luego reemplaza."""
        tmp_file = self.history_file + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(list(self.downloaded_urls), f, indent=4)
            os.replace(tmp_file, self.history_file)
        except Exception as e:
            logger.error(f"No se pudo guardar el historial: {e}")
            if os.path.exists(tmp_file):
                try: os.remove(tmp_file)
                except: pass

    def is_downloaded(self, url: str) -> bool:
        """Devuelve True si la URL ya fue descargada previamente."""
        with self._lock:
            return url in self.downloaded_urls

    def mark_as_downloaded(self, url: str):
        """Marca una URL como descargada. Guarda a disco en batch para reducir I/O."""
        with self._lock:
            self.downloaded_urls.add(url)
            self._pending_saves += 1
            if self._pending_saves >= self.save_every:
                self._save_history()
                self._pending_saves = 0

    def flush(self):
        """Fuerza el guardado inmediato del historial pendiente. Llamar al terminar una sesión."""
        with self._lock:
            if self._pending_saves > 0:
                self._save_history()
                self._pending_saves = 0
