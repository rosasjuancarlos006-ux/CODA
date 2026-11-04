import pytest
from utils.file_manager import sanitize_filename


class TestFileManager:
    """Conjunto de pruebas para utils/file_manager.py."""

    def test_sanitize_normal_name(self):
        assert sanitize_filename("Cancion Normal") == "Cancion Normal"
        assert sanitize_filename("Artist - Title (Audio)") == "Artist - Title (Audio)"

    def test_sanitize_forbidden_windows_characters(self):
        # Caracteres prohibidos en Windows: < > : " / \ | ? *
        raw = 'Bad:Bunny/Moscow\\Mule*Un?Verano<Sin>Ti|Part"1"'
        sanitized = sanitize_filename(raw)
        for char in '<>:"/\\|?*':
            assert char not in sanitized, f"El caracter prohibido '{char}' permanece en el nombre."

    def test_sanitize_trailing_and_leading_spaces(self):
        assert sanitize_filename("  Cancion con espacios  ") == "Cancion con espacios"

    def test_sanitize_unicode_characters(self):
        unicode_title = "Camilo, Carín León - Una Vida Pasada"
        assert sanitize_filename(unicode_title) == unicode_title
