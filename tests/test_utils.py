import pytest
import os
from scrapic.core.utils import FileUtils
from scrapic.core.image_scraper import MultiEngineScraper

def test_clean_filename():
    """Prueba que el sanitizador de nombres de archivo funcione correctamente."""
    assert FileUtils.clean_filename("archivo%20con%20espacios.pdf") == "archivo_con_espacios.pdf"
    assert FileUtils.clean_filename("n0mbr3_r@ro!!.csv") == "n0mbr3_r_ro_.csv"
    assert FileUtils.clean_filename("_____muchos_guiones.txt") == "muchos_guiones.txt"

def test_validate_size(tmp_path):
    """Prueba la validación de tamaño mínimo de archivo (MB)."""
    # Crear un archivo de 2MB falsos
    file_path = tmp_path / "dummy.txt"
    with open(file_path, "wb") as f:
        f.write(b"0" * (2 * 1024 * 1024))
    
    # 2MB cumple con mínimo de 1MB
    assert FileUtils.validate_size(str(file_path), min_size_mb=1.0) == True
    # 2MB NO cumple con mínimo de 3MB
    assert FileUtils.validate_size(str(file_path), min_size_mb=3.0) == False


def test_image_scraper_creates_concept_directory(tmp_path, monkeypatch):
    monkeypatch.setattr("scrapic.core.image_scraper.HistoryManager", lambda: None)
    monkeypatch.setattr("scrapic.core.image_scraper.OSINTReporter", lambda: None)
    scraper = MultiEngineScraper(base_dir=str(tmp_path / "images"))

    concept_dir = scraper.create_concept_dir("test concept")

    assert concept_dir == str(tmp_path / "images" / "test_concept")
    assert os.path.isdir(concept_dir)


@pytest.mark.parametrize("concept", ["../outside", str(os.path.abspath("outside"))])
def test_make_concept_dir_keeps_untrusted_concept_inside_base(tmp_path, concept):
    base = tmp_path / "downloads"

    concept_dir = FileUtils.make_concept_dir(str(base), concept)

    assert os.path.commonpath([str(base.resolve()), concept_dir]) == str(base.resolve())
    assert os.path.isdir(concept_dir)
    assert not (tmp_path / "outside").exists()


def test_make_concept_dir_rejects_dot_directory(tmp_path):
    with pytest.raises(ValueError):
        FileUtils.make_concept_dir(str(tmp_path), "..")


def test_validate_pdf_checks_readability_when_min_pages_is_zero(tmp_path):
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_bytes(b"not a PDF")

    assert FileUtils.validate_pdf(str(pdf_path), min_pages=0) is False


def test_validate_pdf_accepts_readable_pdf_when_min_pages_is_zero(tmp_path):
    from pypdf import PdfWriter

    pdf_path = tmp_path / "valid.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as pdf_file:
        writer.write(pdf_file)

    assert FileUtils.validate_pdf(str(pdf_path)) is True


def test_save_response_removes_partial_file_when_size_limit_is_exceeded(tmp_path):
    from unittest.mock import MagicMock

    response = MagicMock()
    response.headers = {}
    response.iter_content.return_value = [b"1234", b"5678"]
    destination = tmp_path / "partial.bin"

    with pytest.raises(ValueError, match="excede el límite"):
        FileUtils.save_response(response, str(destination), max_bytes=5)

    assert not destination.exists()
    response.close.assert_called_once()


def test_save_response_rejects_declared_size_over_limit_before_writing(tmp_path):
    from unittest.mock import MagicMock

    response = MagicMock()
    response.headers = {"Content-Length": "10"}
    destination = tmp_path / "large.bin"

    with pytest.raises(ValueError, match="excede el límite"):
        FileUtils.save_response(response, str(destination), max_bytes=5)

    assert not destination.exists()
    response.iter_content.assert_not_called()
    response.close.assert_called_once()
