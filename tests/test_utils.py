import pytest
import os
from src.core.utils import FileUtils

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
