import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from main import handle_download_prompt, main


class TestMainOrchestration:
    """Pruebas de orquestación para main.py (Modo Interactivo y CLI)."""

    @patch("main.handle_single_download")
    @patch("ui.display.console.input", return_value="Coldplay Yellow")
    @patch("ui.display.prompt_platform", return_value="youtube")
    def test_handle_download_prompt_interactive_flow_order(self, mock_prompt_platform, mock_input, mock_download):
        call_order = []
        mock_prompt_platform.side_effect = lambda: (call_order.append("platform"), "youtube")[1]
        mock_input.side_effect = lambda *args, **kwargs: (call_order.append("query"), "Coldplay Yellow")[1]

        handle_download_prompt(Path("downloads"))

        assert call_order == ["platform", "query"]
        mock_download.assert_called_once()
        # Verificar que el query enviado a resolver/descargar tiene formato de YouTube general
        resolved_query = mock_download.call_args[0][0]
        assert resolved_query == "ytsearch1:Coldplay Yellow"

    @patch("main.handle_single_download")
    @patch("ui.display.show_platform_mismatch_warning")
    @patch("ui.display.console.input", return_value="https://music.youtube.com/watch?v=123")
    @patch("ui.display.prompt_platform", return_value="youtube")
    def test_handle_download_prompt_auto_adaptation(self, mock_prompt_platform, mock_input, mock_warning, mock_download):
        handle_download_prompt(Path("downloads"))

        mock_warning.assert_called_once_with("youtube", "youtube_music")
        mock_download.assert_called_once()
        # Enlace individual limpio
        assert mock_download.call_args[0][0] == "https://music.youtube.com/watch?v=123"

    @patch("main.handle_single_download")
    @patch("main.parse_arguments")
    def test_cli_direct_youtube_music_inference(self, mock_args, mock_download):
        args = MagicMock()
        args.query = "https://music.youtube.com/watch?v=ABC123XYZ&list=RDABC123XYZ"
        args.output = None
        args.limit = None
        mock_args.return_value = args

        main()

        mock_download.assert_called_once()
        # Debe haber limpiado la URL del mix
        cleaned_url = mock_download.call_args[0][0]
        assert cleaned_url == "https://music.youtube.com/watch?v=ABC123XYZ"
        assert "&list=" not in cleaned_url

    @patch("main.handle_single_download")
    @patch("main.parse_arguments")
    def test_cli_direct_search_defaults_to_youtube(self, mock_args, mock_download):
        args = MagicMock()
        args.query = "Queen Bohemian Rhapsody"
        args.output = None
        args.limit = None
        mock_args.return_value = args

        main()

        mock_download.assert_called_once()
        query = mock_download.call_args[0][0]
        assert query == "ytsearch1:Queen Bohemian Rhapsody"
