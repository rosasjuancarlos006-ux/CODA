from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import main


class TestMainOrchestration:
    """Pruebas de orquestación para el bootstrap en main.py."""

    @patch("main.parse_arguments")
    @patch("main.DownloadController")
    @patch("main.TerminalView")
    def test_main_runs_cli_direct_when_query_provided(self, mock_view_cls, mock_ctrl_cls, mock_args):
        args = MagicMock()
        args.query = "https://youtube.com/watch?v=123"
        args.output = None
        args.format = "mp3"
        args.limit = 5
        mock_args.return_value = args

        mock_ctrl = MagicMock()
        mock_ctrl.run_cli_direct.return_value = 0
        mock_ctrl_cls.return_value = mock_ctrl

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 0
        mock_ctrl.run_cli_direct.assert_called_once_with(
            query="https://youtube.com/watch?v=123",
            requested_format="mp3",
            playlist_limit=5
        )

    @patch("main.parse_arguments")
    @patch("main.DownloadController")
    @patch("main.TerminalView")
    def test_main_runs_interactive_loop_when_no_query(self, mock_view_cls, mock_ctrl_cls, mock_args):
        args = MagicMock()
        args.query = None
        args.output = None
        mock_args.return_value = args

        mock_ctrl = MagicMock()
        mock_ctrl_cls.return_value = mock_ctrl

        main.main()

        mock_ctrl.run_interactive_loop.assert_called_once()

    @patch("main.parse_arguments")
    @patch("main.DownloadController")
    def test_main_handles_keyboard_interrupt(self, mock_ctrl_cls, mock_args):
        mock_args.side_effect = KeyboardInterrupt

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 0

    @patch("main.parse_arguments")
    def test_main_handles_critical_exception(self, mock_args):
        mock_args.side_effect = RuntimeError("Error fatal simulado")

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 1
