import csv
import os
import threading
import pytest
from src.core.report import OSINTReporter


@pytest.fixture
def reporter(tmp_path):
    """Crea un OSINTReporter con archivo temporal para cada test."""
    return OSINTReporter(report_file=str(tmp_path / "test_reporte.csv"))


def test_csv_created_on_init(tmp_path):
    """El archivo CSV se crea automáticamente al instanciar el reporter."""
    report_file = str(tmp_path / "auto_created.csv")
    assert not os.path.exists(report_file)
    OSINTReporter(report_file=report_file)
    assert os.path.exists(report_file)


def test_csv_has_correct_headers(reporter):
    """El CSV contiene las columnas correctas en la primera fila."""
    with open(reporter.report_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert headers == ["Fecha_Hora", "Archivo_Local", "URL_Origen", "Mision_Origen", "Tamano_MB"]


def test_log_download_writes_row(reporter, tmp_path):
    """log_download() escribe una fila con los datos correctos."""
    # Crear un archivo real para que el reporter pueda medir su tamaño
    fake_file = tmp_path / "imagen_001.jpg"
    fake_file.write_bytes(b"x" * (100 * 1024))  # 100 KB → 0.09 MB

    reporter.log_download(str(fake_file), "https://fuente.com/img.jpg", "Image Scraper (bing)")

    with open(reporter.report_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # saltar headers
        row = next(reader)

    assert row[1] == str(fake_file)
    assert row[2] == "https://fuente.com/img.jpg"
    assert row[3] == "Image Scraper (bing)"
    # El tamaño debe ser > 0 (el archivo existe)
    assert float(row[4]) > 0


def test_log_download_nonexistent_file(reporter):
    """log_download() no falla si el archivo no existe — registra tamaño 0."""
    reporter.log_download("/ruta/que/no/existe.pdf", "https://url.com/doc.pdf", "Spider")

    with open(reporter.report_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # saltar headers
        row = next(reader)

    assert row[4] == "0.00"


def test_multiple_rows(reporter, tmp_path):
    """Múltiples llamadas agregan múltiples filas, no sobreescriben."""
    for i in range(3):
        fake_file = tmp_path / f"doc_{i}.pdf"
        fake_file.write_bytes(b"y" * 512)
        reporter.log_download(str(fake_file), f"https://fuente.com/doc_{i}.pdf", "Dataset")

    with open(reporter.report_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # 1 fila de headers + 3 de datos
    assert len(rows) == 4


def test_thread_safe_concurrent_writes(reporter, tmp_path):
    """Escrituras concurrentes desde múltiples hilos no corrompen el CSV."""
    fake_file = tmp_path / "concurrent.jpg"
    fake_file.write_bytes(b"z" * 100)

    def write_row(i):
        reporter.log_download(str(fake_file), f"https://concurrent-{i}.com/img.jpg", "Test")

    threads = [threading.Thread(target=write_row, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    with open(reporter.report_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # 1 header + 20 filas de datos, sin corrupción
    assert len(rows) == 21
