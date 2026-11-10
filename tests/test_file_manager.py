import time
from pathlib import Path
import pytest
from utils.file_manager import (
    sanitize_filename,
    AudioFileInfo,
    SUPPORTED_AUDIO_EXTENSIONS,
    scan_audio_downloads,
    find_partial_download_files,
    cleanup_files,
)


class TestFileManager:
    """Conjunto de pruebas para utils/file_manager.py."""

    def test_sanitize_normal_name(self):
        assert sanitize_filename("Cancion Normal") == "Cancion Normal"
        assert sanitize_filename("Artist - Title (Audio)") == "Artist - Title (Audio)"

    def test_sanitize_forbidden_windows_characters(self):
        raw = 'Bad:Bunny/Moscow\\Mule*Un?Verano<Sin>Ti|Part"1"'
        sanitized = sanitize_filename(raw)
        for char in '<>:"/\\|?*':
            assert char not in sanitized, f"El caracter prohibido '{char}' permanece en el nombre."

    def test_sanitize_trailing_and_leading_spaces(self):
        assert sanitize_filename("  Cancion con espacios  ") == "Cancion con espacios"

    def test_sanitize_unicode_characters(self):
        unicode_title = "Camilo, Carín León - Una Vida Pasada"
        assert sanitize_filename(unicode_title) == unicode_title

    def test_supported_audio_extensions_constant(self):
        assert {".mp3", ".m4a", ".opus"} == SUPPORTED_AUDIO_EXTENSIONS

    def test_scan_audio_downloads_filters_and_sorts(self, tmp_path: Path):
        # Crear archivos con distintas extensiones y marcas de tiempo
        old_mp3 = tmp_path / "01_old_song.mp3"
        old_mp3.write_text("audio1")
        
        # Simular diferencia de tiempo
        new_opus = tmp_path / "02_new_song.opus"
        new_opus.write_text("audio2")

        new_m4a = tmp_path / "03_newer_song.m4a"
        new_m4a.write_text("audio3")

        # Archivos no soportados que deben ignorarse
        (tmp_path / "readme.txt").write_text("info")
        (tmp_path / "cover.jpg").write_text("image")
        (tmp_path / "partial.part").write_text("temp")

        results = scan_audio_downloads(tmp_path)
        assert len(results) == 3
        
        # Verificar tipos e información
        names = [r.name for r in results]
        assert "01_old_song.mp3" in names
        assert "02_new_song.opus" in names
        assert "03_newer_song.m4a" in names
        assert "readme.txt" not in names
        assert "cover.jpg" not in names
        assert "partial.part" not in names

        for item in results:
            assert isinstance(item, AudioFileInfo)
            assert item.format in {"mp3", "m4a", "opus"}
            assert item.size_bytes > 0

    def test_scan_audio_downloads_empty_or_nonexistent(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert scan_audio_downloads(empty_dir) == []

        non_existent = tmp_path / "non_existent"
        assert scan_audio_downloads(non_existent) == []

    def test_find_partial_download_files(self, tmp_path: Path):
        # Archivo previo al inicio de la descarga
        pre_existing = tmp_path / "previous_song.mp3"
        pre_existing.write_text("old")
        
        # Simulamos marca de tiempo de inicio
        time.sleep(0.05)
        start_time = time.time()
        time.sleep(0.05)

        # Archivos creados durante la descarga
        partial_part = tmp_path / "downloading.mp3.part"
        partial_part.write_text("partial stream")
        
        partial_ytdl = tmp_path / "stream.ytdl"
        partial_ytdl.write_text("ytdl stream")

        new_audio = tmp_path / "interrupted.opus"
        new_audio.write_text("audio not finished")

        partials = find_partial_download_files(tmp_path, start_time)
        partial_names = [p.name for p in partials]

        assert "downloading.mp3.part" in partial_names
        assert "stream.ytdl" in partial_names
        assert "interrupted.opus" in partial_names
        assert "previous_song.mp3" not in partial_names

    def test_cleanup_files(self, tmp_path: Path):
        f1 = tmp_path / "file1.part"
        f1.write_text("data")
        f2 = tmp_path / "file2.temp"
        f2.write_text("data")
        non_existent = tmp_path / "ghost.mp3"

        deleted = cleanup_files([f1, f2, non_existent])
        assert deleted == 2
        assert not f1.exists()
        assert not f2.exists()
