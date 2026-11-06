import pytest
from unittest.mock import patch
from ui.display import (
    prompt_platform,
    get_platform_display_name,
    show_platform_mismatch_warning
)


class TestDisplayPlatform:
    """Pruebas unitarias para los componentes de plataforma en ui/display.py."""

    def test_get_platform_display_name(self):
        assert get_platform_display_name("youtube") == "YouTube"
        assert get_platform_display_name("youtube_music") == "YouTube Music"
        # Fallback para cadenas no mapeadas
        assert get_platform_display_name("otra") == "otra"

    @patch("rich.console.Console.input", return_value="")
    def test_prompt_platform_default_empty_input(self, mock_input):
        result = prompt_platform()
        assert result == "youtube"

    @patch("rich.console.Console.input", return_value="2")
    def test_prompt_platform_youtube_music_option(self, mock_input):
        result = prompt_platform()
        assert result == "youtube_music"

    @patch("rich.console.Console.input", return_value="music")
    def test_prompt_platform_youtube_music_alias(self, mock_input):
        result = prompt_platform()
        assert result == "youtube_music"

    @patch("rich.console.Console.input", side_effect=["invalid1", "invalid2", "invalid3"])
    def test_prompt_platform_max_retries_fallback(self, mock_input):
        result = prompt_platform()
        assert result == "youtube"

    @patch("rich.console.Console.input", side_effect=KeyboardInterrupt)
    def test_prompt_platform_keyboard_interrupt(self, mock_input):
        with pytest.raises(KeyboardInterrupt):
            prompt_platform()

    def test_show_platform_mismatch_warning_output(self, capsys):
        # Asegurar que se ejecuta sin lanzar excepción
        show_platform_mismatch_warning("youtube", "youtube_music")
