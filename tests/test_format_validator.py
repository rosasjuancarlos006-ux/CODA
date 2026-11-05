import pytest
from utils.format_validator import (
    SUPPORTED_FORMATS,
    DEFAULT_FORMAT,
    normalize_format_input,
    is_valid_format,
    resolve_audio_format
)


class TestFormatValidator:
    """Suite de pruebas unitarias para utils/format_validator.py."""

    def test_constants(self):
        assert DEFAULT_FORMAT == "mp3"
        assert "mp3" in SUPPORTED_FORMATS
        assert "m4a" in SUPPORTED_FORMATS
        assert "opus" in SUPPORTED_FORMATS

    def test_normalize_format_input_with_valid_data(self):
        assert normalize_format_input("MP3") == "mp3"
        assert normalize_format_input("  opus  ") == "opus"
        assert normalize_format_input("M4a") == "m4a"

    def test_normalize_format_input_with_empty_or_whitespace(self):
        assert normalize_format_input("") == ""
        assert normalize_format_input("    ") == ""
        assert normalize_format_input(None) == ""

    def test_is_valid_format_success(self):
        for fmt in ("mp3", "m4a", "opus"):
            assert is_valid_format(fmt) is True

    def test_is_valid_format_unsupported(self):
        unsupported = ("flac", "wav", "aac", "ogg", "mp4", "video", "123")
        for fmt in unsupported:
            assert is_valid_format(fmt) is False

    def test_is_valid_format_extreme_lengths(self):
        long_string = "a" * 25
        assert is_valid_format(long_string) is False

    def test_resolve_audio_format_default(self):
        # Entradas vacías o de sólo espacios retornan el default
        assert resolve_audio_format("") == (True, "mp3")
        assert resolve_audio_format("   ") == (True, "mp3")
        assert resolve_audio_format(None) == (True, "mp3")

    def test_resolve_audio_format_explicit(self):
        assert resolve_audio_format("opus") == (True, "opus")
        assert resolve_audio_format(" M4A ") == (True, "m4a")
        assert resolve_audio_format("MP3") == (True, "mp3")

    def test_resolve_audio_format_invalid(self):
        assert resolve_audio_format("flac") == (False, "")
        assert resolve_audio_format("mp5") == (False, "")
        assert resolve_audio_format("musica") == (False, "")
