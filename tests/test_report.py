import os
import threading
import sqlite3
import pytest
from src.core.report import OSINTReporter
from src.core.database import DatabaseManager

@pytest.fixture(autouse=True)
def reset_db_singleton():
    """Resetea el singleton para evitar conflictos entre tests."""
    DatabaseManager._instance = None
    yield
    DatabaseManager._instance = None

@pytest.fixture
def reporter(tmp_path):
    """Crea un OSINTReporter con BD temporal para cada test."""
    return OSINTReporter(report_file=str(tmp_path / "test_reporte.db"))

def test_db_created_on_init(tmp_path):
    """El archivo .db se crea automáticamente al instanciar el reporter."""
    report_file = str(tmp_path / "auto_created.db")
    assert not os.path.exists(report_file)
    OSINTReporter(report_file=report_file)
    assert os.path.exists(report_file)

def test_db_has_correct_tables(reporter):
    """La BD contiene la tabla de downloads."""
    conn = sqlite3.connect(reporter.report_file)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'")
    assert cur.fetchone() is not None
    conn.close()

def test_log_download_writes_row(reporter, tmp_path):
    """log_download() escribe un registro en la BD."""
    fake_file = tmp_path / "imagen_001.jpg"
    fake_file.write_bytes(b"x" * (100 * 1024))  # 100 KB

    reporter.log_download(str(fake_file), "https://fuente.com/img.jpg", "Image Scraper (bing)")

    conn = sqlite3.connect(reporter.report_file)
    cur = conn.execute("SELECT * FROM downloads")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[2] == str(fake_file) # filepath
    assert row[1] == "https://fuente.com/img.jpg" # url
    assert row[3] == "Image Scraper (bing)" # source
    assert float(row[4]) > 0 # size_mb

def test_log_download_nonexistent_file(reporter):
    """log_download() no falla si el archivo no existe — registra tamaño 0."""
    reporter.log_download("/ruta/que/no/existe.pdf", "https://url.com/doc.pdf", "Spider")

    conn = sqlite3.connect(reporter.report_file)
    cur = conn.execute("SELECT size_mb FROM downloads")
    row = cur.fetchone()
    conn.close()

    assert row[0] == 0.0

def test_multiple_rows(reporter, tmp_path):
    """Múltiples llamadas agregan múltiples registros."""
    for i in range(3):
        fake_file = tmp_path / f"doc_{i}.pdf"
        fake_file.write_bytes(b"y" * 512)
        reporter.log_download(str(fake_file), f"https://fuente.com/doc_{i}.pdf", "Dataset")

    conn = sqlite3.connect(reporter.report_file)
    cur = conn.execute("SELECT COUNT(*) FROM downloads")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 3

def test_thread_safe_concurrent_writes(reporter, tmp_path):
    """Escrituras concurrentes desde múltiples hilos son seguras en SQLite."""
    fake_file = tmp_path / "concurrent.jpg"
    fake_file.write_bytes(b"z" * 100)

    def write_row(i):
        reporter.log_download(str(fake_file), f"https://concurrent-{i}.com/img.jpg", "Test")

    threads = [threading.Thread(target=write_row, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    conn = sqlite3.connect(reporter.report_file)
    cur = conn.execute("SELECT COUNT(*) FROM downloads")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 20
