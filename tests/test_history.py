import os
import sqlite3
import threading
import pytest
from src.core.history import HistoryManager
from src.core.database import DatabaseManager

@pytest.fixture(autouse=True)
def reset_db_singleton():
    """Resetea el singleton para evitar conflictos de bloqueos en tests."""
    DatabaseManager._instance = None
    yield
    DatabaseManager._instance = None

@pytest.fixture
def history(tmp_path):
    """Crea un HistoryManager con BD temporal."""
    return HistoryManager(history_file=str(tmp_path / "test_history.db"))


def test_is_downloaded_false_on_fresh_instance(history):
    """Un historial vacío siempre devuelve False."""
    assert history.is_downloaded("https://ejemplo.com/imagen.jpg") is False


def test_mark_and_check(history):
    """Después de marcar una URL, is_downloaded devuelve True."""
    url = "https://ejemplo.com/foto.png"
    history.mark_as_downloaded(url)
    assert history.is_downloaded(url) is True


def test_unrelated_url_still_false(history):
    """Marcar una URL no afecta a otras URLs."""
    history.mark_as_downloaded("https://a.com/foto.png")
    assert history.is_downloaded("https://b.com/otro.png") is False


def test_flush_does_not_break(history):
    """flush() ya no hace I/O por batch, pero no debe fallar por compatibilidad."""
    history.mark_as_downloaded("https://pendiente.com/archivo.pdf")
    history.flush()
    assert history.is_downloaded("https://pendiente.com/archivo.pdf")


def test_persistence_across_instances(tmp_path):
    """Las URLs guardadas persisten cuando se crea una nueva instancia apuntando a la misma DB."""
    db_file = str(tmp_path / "persist_test.db")
    url = "https://persistente.com/doc.pdf"

    h1 = HistoryManager(history_file=db_file)
    h1.mark_as_downloaded(url)

    DatabaseManager._instance = None  # Forzar nueva conexión
    h2 = HistoryManager(history_file=db_file)
    assert h2.is_downloaded(url) is True


def test_thread_safety(history):
    """Escrituras concurrentes no fallan gracias al SQLite Manager."""
    urls = [f"https://thread-test-{i}.com/img.jpg" for i in range(50)]
    threads = [threading.Thread(target=history.mark_as_downloaded, args=(url,)) for url in urls]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for url in urls:
        assert history.is_downloaded(url) is True, f"URL perdida: {url}"


def test_duplicate_url_not_duplicated(history):
    """Marcar la misma URL dos veces no lanza error (INSERT OR IGNORE)."""
    url = "https://duplicado.com/img.jpg"
    history.mark_as_downloaded(url)
    history.mark_as_downloaded(url)
    
    conn = sqlite3.connect(history.db.db_path)
    cur = conn.execute("SELECT COUNT(*) FROM history WHERE url = ?", (url,))
    count = cur.fetchone()[0]
    conn.close()
    
    assert count == 1
