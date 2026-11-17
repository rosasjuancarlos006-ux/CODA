import pytest
from pathlib import Path
import time

def test_resolve_incremental_filename_no_collision(tmp_path: Path):
    """
    Verifica que si el archivo no existe, retorna el nombre base con su extensión.
    """
    from utils.file_manager import resolve_incremental_filename

    res = resolve_incremental_filename(tmp_path, "Cancion", ".mp3")
    assert res == tmp_path / "Cancion.mp3"


def test_resolve_incremental_filename_single_collision(tmp_path: Path):
    """
    Verifica que si Cancion.mp3 ya existe, genera Cancion (1).mp3.
    """
    from utils.file_manager import resolve_incremental_filename

    (tmp_path / "Cancion.mp3").touch()

    res = resolve_incremental_filename(tmp_path, "Cancion", ".mp3")
    assert res == tmp_path / "Cancion (1).mp3"


def test_resolve_incremental_filename_multiple_collisions(tmp_path: Path):
    """
    Verifica que ante Cancion.mp3, Cancion (1).mp3 y Cancion (2).mp3, genera Cancion (3).mp3.
    """
    from utils.file_manager import resolve_incremental_filename

    (tmp_path / "Cancion.mp3").touch()
    (tmp_path / "Cancion (1).mp3").touch()
    (tmp_path / "Cancion (2).mp3").touch()

    res = resolve_incremental_filename(tmp_path, "Cancion", ".mp3")
    assert res == tmp_path / "Cancion (3).mp3"


def test_resolve_incremental_filename_sanitizes_reserved_characters(tmp_path: Path):
    """
    Verifica que sanea caracteres reservados de Windows en el base_title antes de resolver.
    """
    from utils.file_manager import resolve_incremental_filename

    # Caracteres ilegales en Windows: : / \ ? * < > | "
    res = resolve_incremental_filename(tmp_path, 'Cancion: "Especial" / *Prueba*', ".m4a")
    assert ":" not in res.name
    assert '"' not in res.name
    assert "/" not in res.name
    assert "*" not in res.name
    assert res.suffix == ".m4a"


def test_resolve_incremental_filename_formats_extension_dot(tmp_path: Path):
    """
    Verifica que normalice si la extensión se pasa sin punto (ej: 'opus' -> '.opus').
    """
    from utils.file_manager import resolve_incremental_filename

    res = resolve_incremental_filename(tmp_path, "Audio", "opus")
    assert res.name == "Audio.opus"


def test_scan_downloaded_audio_metadata_returns_formatted_dicts(tmp_path: Path):
    """
    Verifica que scan_downloaded_audio_metadata devuelva una lista de diccionarios
    con metadatos legibles (name, format, size_str, date_str, path) ordenados por fecha descendente
    y filtrando solo extensiones soportadas (.mp3, .m4a, .opus).
    """
    from utils.file_manager import scan_downloaded_audio_metadata

    # Crear archivos soportados y no soportados
    f_mp3 = tmp_path / "pista1.mp3"
    f_mp3.write_bytes(b"A" * 1024)  # 1 KB

    f_txt = tmp_path / "notas.txt"
    f_txt.write_bytes(b"B" * 500)

    f_m4a = tmp_path / "pista2.m4a"
    f_m4a.write_bytes(b"C" * (1024 * 1024 * 2))  # 2 MB

    items = scan_downloaded_audio_metadata(tmp_path)
    assert len(items) == 2

    names = [i["name"] for i in items]
    assert "pista1.mp3" in names
    assert "pista2.m4a" in names
    assert "notas.txt" not in names

    # Comprobar llaves requeridas
    for item in items:
        assert "name" in item
        assert "format" in item
        assert "size_bytes" in item
        assert "size_str" in item
        assert "date_str" in item
        assert "path" in item


def test_scan_downloaded_audio_metadata_empty_or_nonexistent(tmp_path: Path):
    """
    Verifica que devuelva lista vacía si el directorio no existe o no tiene audios.
    """
    from utils.file_manager import scan_downloaded_audio_metadata

    assert scan_downloaded_audio_metadata(tmp_path / "inexistente") == []

    empty_dir = tmp_path / "vacio"
    empty_dir.mkdir()
    assert scan_downloaded_audio_metadata(empty_dir) == []
