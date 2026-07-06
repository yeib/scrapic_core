import json
import os
import threading
import pytest
from src.core.history import HistoryManager


@pytest.fixture
def history(tmp_path):
    """Crea un HistoryManager con archivo temporal para cada test."""
    return HistoryManager(history_file=str(tmp_path / "test_history.json"), save_every=10)


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


def test_batch_save_only_at_threshold(tmp_path):
    """El archivo NO se escribe a disco antes de alcanzar save_every marcas."""
    history_file = str(tmp_path / "batch_test.json")
    h = HistoryManager(history_file=history_file, save_every=5)

    # 4 marcas — por debajo del umbral, no se guarda en disco
    for i in range(4):
        h.mark_as_downloaded(f"https://test-{i}.com")
    assert not os.path.exists(history_file), "No debería guardar antes del umbral"

    # La 5ta marca supera el umbral y dispara el guardado
    h.mark_as_downloaded("https://test-5.com")
    assert os.path.exists(history_file), "Debería haber guardado al alcanzar el umbral"


def test_flush_saves_pending(tmp_path):
    """flush() guarda a disco aunque no se haya alcanzado el umbral."""
    history_file = str(tmp_path / "flush_test.json")
    h = HistoryManager(history_file=history_file, save_every=100)

    h.mark_as_downloaded("https://pendiente.com/archivo.pdf")
    assert not os.path.exists(history_file), "No debería haber guardado aún"

    h.flush()
    assert os.path.exists(history_file), "flush() debe forzar el guardado"
    with open(history_file) as f:
        data = json.load(f)
    assert "https://pendiente.com/archivo.pdf" in data


def test_persistence_across_instances(tmp_path):
    """Las URLs guardadas persisten cuando se crea una nueva instancia del manager."""
    history_file = str(tmp_path / "persist_test.json")
    url = "https://persistente.com/doc.pdf"

    h1 = HistoryManager(history_file=history_file, save_every=1)
    h1.mark_as_downloaded(url)

    # Nueva instancia carga desde el mismo archivo
    h2 = HistoryManager(history_file=history_file)
    assert h2.is_downloaded(url) is True


def test_thread_safety(history):
    """Escrituras concurrentes desde múltiples hilos no corrompen el historial."""
    urls = [f"https://thread-test-{i}.com/img.jpg" for i in range(50)]
    threads = [threading.Thread(target=history.mark_as_downloaded, args=(url,)) for url in urls]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    history.flush()
    for url in urls:
        assert history.is_downloaded(url) is True, f"URL perdida: {url}"


def test_duplicate_url_not_duplicated(history):
    """Marcar la misma URL dos veces no genera duplicados en el set."""
    url = "https://duplicado.com/img.jpg"
    history.mark_as_downloaded(url)
    history.mark_as_downloaded(url)
    assert len(history.downloaded_urls) == 1
