from io import StringIO
from pathlib import Path
from unittest.mock import patch
import pytest

from core.events import DownloadPhase, ProgressEvent
from ui.terminal_view import TerminalView
from ui.view_interface import ViewInterface
from utils.file_manager import AudioFileInfo


class TestTerminalView:
    def test_implements_view_interface(self):
        view = TerminalView()
        assert isinstance(view, ViewInterface)

    def test_show_empty_downloads(self):
        view = TerminalView()
        # Should not raise exception
        view.show_empty_downloads()

    def test_show_downloads_table(self):
        view = TerminalView()
        downloads = [
            AudioFileInfo(
                name="Song 1.mp3",
                path=Path("downloads/Song 1.mp3"),
                format="mp3",
                size_bytes=3_500_000,
                modified_timestamp=1700000000.0,
            ),
            AudioFileInfo(
                name="Song 2.opus",
                path=Path("downloads/Song 2.opus"),
                format="opus",
                size_bytes=1_200_000,
                modified_timestamp=1700000100.0,
            ),
        ]
        # Should render without crashing
        view.show_downloads_table(downloads)

    def test_prompt_query(self):
        view = TerminalView()
        with patch.object(view.console, "input", return_value="  https://youtube.com/watch?v=123  "):
            result = view.prompt_query("YouTube")
            assert result == "https://youtube.com/watch?v=123"

    def test_prompt_playlist_limit_valid_number(self):
        view = TerminalView()
        with patch.object(view.console, "input", return_value="10"):
            limit = view.prompt_playlist_limit()
            assert limit == 10

    def test_prompt_playlist_limit_empty_returns_none(self):
        view = TerminalView()
        with patch.object(view.console, "input", return_value=""):
            limit = view.prompt_playlist_limit()
            assert limit is None

    def test_on_progress_with_metrics_and_degradation(self):
        view = TerminalView()
        # Iniciar tarea
        view.start_progress_task("Descarga de prueba", total=100)

        # Evento con métricas completas
        event_with_metrics = ProgressEvent(
            phase=DownloadPhase.DOWNLOADING,
            percentage=50.0,
            speed_bytes_sec=1024 * 1024,
            eta_seconds=5,
            item_title="Test Song"
        )
        view.on_progress(event_with_metrics)

        # Evento con degradación (sin porcentaje ni velocidad)
        event_without_metrics = ProgressEvent(
            phase=DownloadPhase.CONVERTING,
            percentage=None,
            speed_bytes_sec=None,
            eta_seconds=None,
            message="Convirtiendo audio vía FFmpeg..."
        )
        view.on_progress(event_without_metrics)

        # Finalizar
        view.stop_progress_task()
