import sqlite3
import threading
import logging
from typing import List, Dict

logger = logging.getLogger("scrapic")

class DatabaseManager:
    """Manejador central de la base de datos SQLite para Scrapic (Thread-safe)."""
    
    def __init__(self, db_path: str = "scrapic.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.thread_local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self.thread_local, "conn"):
            self.thread_local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.thread_local.conn.row_factory = sqlite3.Row
        return self.thread_local.conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        source TEXT NOT NULL,
                        size_mb REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        url TEXT PRIMARY KEY
                    )
                ''')
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error inicializando base de datos SQLite: {e}")

    # --- OSINT Reporter Methods ---
    def log_download(self, url: str, filepath: str, source: str, size_mb: float):
        conn = self._get_conn()
        try:
            with self._lock:
                conn.execute('''
                    INSERT INTO downloads (url, filepath, source, size_mb)
                    VALUES (?, ?, ?, ?)
                ''', (url, filepath, source, size_mb))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error registrando descarga en DB: {e}")
            
    def get_all_downloads(self) -> List[Dict]:
        conn = self._get_conn()
        cur = conn.execute("SELECT * FROM downloads ORDER BY timestamp DESC")
        return [dict(row) for row in cur.fetchall()]

    # --- History Manager Methods ---
    def is_downloaded(self, url: str) -> bool:
        conn = self._get_conn()
        cur = conn.execute("SELECT 1 FROM history WHERE url = ?", (url,))
        return cur.fetchone() is not None

    def mark_as_downloaded(self, url: str):
        conn = self._get_conn()
        try:
            with self._lock:
                conn.execute("INSERT OR IGNORE INTO history (url) VALUES (?)", (url,))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error guardando historial en DB: {e}")
