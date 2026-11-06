import pytest
from utils.platform_validator import (
    SUPPORTED_PLATFORMS,
    DEFAULT_PLATFORM,
    PLATFORM_DISPLAY_NAMES,
    normalize_platform_input,
    detect_url_platform,
    check_platform_mismatch
)


class TestPlatformValidator:
    """Suite de pruebas unitarias para utils/platform_validator.py."""

    def test_constants(self):
        assert DEFAULT_PLATFORM == "youtube"
        assert "youtube" in SUPPORTED_PLATFORMS
        assert "youtube_music" in SUPPORTED_PLATFORMS
        assert PLATFORM_DISPLAY_NAMES["youtube"] == "YouTube"
        assert PLATFORM_DISPLAY_NAMES["youtube_music"] == "YouTube Music"

    def test_normalize_platform_default(self):
        assert normalize_platform_input("") == (True, "youtube")
        assert normalize_platform_input("   ") == (True, "youtube")
        assert normalize_platform_input(None) == (True, "youtube")

    def test_normalize_platform_youtube_aliases(self):
        aliases = ["1", "youtube", "yt", "YT", "  YouTube  "]
        for alias in aliases:
            assert normalize_platform_input(alias) == (True, "youtube")

    def test_normalize_platform_youtube_music_aliases(self):
        aliases = [
            "2",
            "music",
            "ytmusic",
            "YouTube Music",
            "yt_music",
            "youtube   music"  # espacios múltiples colapsados
        ]
        for alias in aliases:
            assert normalize_platform_input(alias) == (True, "youtube_music")

    def test_normalize_platform_invalid(self):
        invalid = ["spotify", "3", "apple", "xyz", "soundcloud"]
        for item in invalid:
            assert normalize_platform_input(item) == (False, None)

    def test_detect_url_platform(self):
        assert detect_url_platform("https://music.youtube.com/watch?v=123") == "youtube_music"
        assert detect_url_platform("http://www.music.youtube.com/playlist?list=PL1") == "youtube_music"
        assert detect_url_platform("https://www.youtube.com/watch?v=123") == "youtube"
        assert detect_url_platform("https://youtu.be/123") == "youtube"
        assert detect_url_platform("cancion sin url") is None
        assert detect_url_platform("https://spotify.com/track/123") is None
        assert detect_url_platform("") is None
        assert detect_url_platform(None) is None

    def test_check_platform_mismatch(self):
        # Discrepancias (debe auto-adaptar)
        assert check_platform_mismatch("youtube", "https://music.youtube.com/watch?v=123") == (True, "youtube_music")
        assert check_platform_mismatch("youtube_music", "https://www.youtube.com/watch?v=123") == (True, "youtube")
        assert check_platform_mismatch("youtube_music", "https://youtu.be/123") == (True, "youtube")

        # Sin discrepancia
        assert check_platform_mismatch("youtube", "https://www.youtube.com/watch?v=123") == (False, "youtube")
        assert check_platform_mismatch("youtube_music", "https://music.youtube.com/watch?v=123") == (False, "youtube_music")

        # Texto libre o URL no reconocida no provocan discrepancia
        assert check_platform_mismatch("youtube", "Coldplay Yellow") == (False, "youtube")
        assert check_platform_mismatch("youtube_music", "Coldplay Yellow") == (False, "youtube_music")
