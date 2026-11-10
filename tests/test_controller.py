from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import pytest

from core.events import ProgressEvent
from utils.file_manager import AudioFileInfo
from controllers.download_controller import DownloadController


class FakeView:
    """Implementación simulada en memoria de ViewInterface para testing determinista."""

    def __init__(self, inputs: Optional[List[str]] = None):
        self.inputs: List[str] = inputs or []
        self.messages_info: List[str] = []
        self.messages_warning: List[str] = []
        self.messages_error: List[str] = []
        self.shown_menus: int = 0
        self.single_successes: List[Dict[str, Any]] = []
        self.playlist_summaries: List[Dict[str, Any]] = []
        self.shown_tables: List[List[AudioFileInfo]] = []
        self.empty_downloads_called: int = 0
        self.mismatches_shown: List[tuple] = []
        self.progress_events: List[ProgressEvent] = []

    def show_banner(self) -> None:
        pass

    def show_main_menu(self) -> str:
        self.shown_menus += 1
        return self.inputs.pop(0) if self.inputs else "3"

    def prompt_platform(self) -> str:
        return self.inputs.pop(0) if self.inputs else "youtube"

    def prompt_query(self, platform_name: str) -> str:
        return self.inputs.pop(0) if self.inputs else "test song"

    def prompt_playlist_limit(self) -> Optional[int]:
        val = self.inputs.pop(0) if self.inputs else None
        return int(val) if val is not None and val.isdigit() else None

    def prompt_audio_format(self, is_playlist: bool) -> str:
        return self.inputs.pop(0) if self.inputs else "mp3"

    def show_platform_mismatch(self, selected: str, adapted: str) -> None:
        self.mismatches_shown.append((selected, adapted))

    def show_info(self, message: str) -> None:
        self.messages_info.append(message)

    def show_warning(self, message: str) -> None:
        self.messages_warning.append(message)

    def show_error(self, message: str, error_type: Optional[str] = None) -> None:
        self.messages_error.append(message)

    def show_single_success(self, result: Dict[str, Any]) -> None:
        self.single_successes.append(result)

    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None:
        self.playlist_summaries.append(summary)

    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None:
        self.shown_tables.append(downloads)

    def show_empty_downloads(self) -> None:
        self.empty_downloads_called += 1

    def on_progress(self, event: ProgressEvent) -> None:
        self.progress_events.append(event)

    def start_progress_task(self, title: str, total: Optional[int] = None) -> None:
        pass

    def stop_progress_task(self) -> None:
        pass


class TestDownloadController:
    def test_run_cli_direct_success(self, tmp_path: Path):
        """RF-04: Modo CLI directo exitoso retorna código 0."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube") as mock_down:
            mock_down.return_value = {
                "success": True,
                "title": "Song",
                "uploader": "Artist",
                "mp3_path": str(tmp_path / "Song.mp3")
            }
            code = controller.run_cli_direct("https://youtube.com/watch?v=123", requested_format="mp3")
            assert code == 0
            assert len(view.single_successes) == 1

    def test_run_cli_direct_failure_returns_non_zero(self, tmp_path: Path):
        """RF-04: Modo CLI directo ante fallo retorna código 1."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube") as mock_down:
            mock_down.return_value = {
                "success": False,
                "error": "download_failed",
                "message": "Video no disponible"
            }
            code = controller.run_cli_direct("https://youtube.com/watch?v=bad")
            assert code == 1
            assert len(view.messages_error) == 1

    def test_run_cli_direct_interrupt_returns_130(self, tmp_path: Path):
        """RF-03, RF-04: Interrupción en CLI directo retorna 130 y limpia archivos."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube", side_effect=KeyboardInterrupt):
            code = controller.run_cli_direct("https://youtube.com/watch?v=123")
            assert code == 130
            assert any("interrumpida" in m.lower() for m in view.messages_warning)

    def test_run_cli_direct_playlist_success(self, tmp_path: Path):
        """RF-04: Modo CLI directo para playlist exitoso retorna código 0."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_playlist") as mock_playlist:
            mock_playlist.return_value = {
                "success": True,
                "playlist_title": "Top Hits",
                "successful": [{"index": 1, "title": "Track 1"}],
                "failed": []
            }
            code = controller.run_cli_direct("https://youtube.com/playlist?list=PL123", playlist_limit=5)
            assert code == 0
            assert len(view.playlist_summaries) == 1

    def test_run_interactive_loop_exit(self, tmp_path: Path):
        """RF-01, RF-02: Bucle interactivo con opción '3' sale limpiamente."""
        view = FakeView(inputs=["3"])
        controller = DownloadController(view=view, output_dir=tmp_path)
        controller.run_interactive_loop()
        assert view.shown_menus == 1
        assert any("gracias" in m.lower() for m in view.messages_info)

    def test_handle_view_downloads_empty(self, tmp_path: Path):
        """RF-06: Ver descargas en carpeta vacía llama a show_empty_downloads."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)
        controller.handle_view_downloads()
        assert view.empty_downloads_called == 1

    def test_handle_view_downloads_with_files(self, tmp_path: Path):
        """RF-06: Ver descargas cuando hay archivos renderiza tabla estructurada."""
        view = FakeView()
        controller = DownloadController(view=view, output_dir=tmp_path)
        (tmp_path / "song.mp3").write_text("mp3 content")

        controller.handle_view_downloads()
        assert len(view.shown_tables) == 1
        assert view.shown_tables[0][0].name == "song.mp3"

    def test_handle_interactive_download_empty_input_retries(self, tmp_path: Path):
        """RF-02: Entrada vacía reintenta sin cerrar el programa."""
        # Usuario ingresa vacío, espacios, y luego una canción válida
        view = FakeView(inputs=["youtube", "", "   ", "Coldplay Clocks", "mp3"])
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube") as mock_down:
            mock_down.return_value = {
                "success": True,
                "title": "Coldplay Clocks",
                "uploader": "Coldplay",
                "mp3_path": str(tmp_path / "Coldplay Clocks.mp3")
            }
            controller.handle_interactive_download()
            # Debe haber mostrado al menos dos advertencias de entrada vacía
            assert len([m for m in view.messages_warning if "no ingresaste" in m.lower()]) >= 2
            assert len(view.single_successes) == 1

    def test_handle_interactive_download_cancel_escape(self, tmp_path: Path):
        """RF-02: Escribir 'cancelar' en el prompt de consulta regresa al menú."""
        view = FakeView(inputs=["youtube", "cancelar"])
        controller = DownloadController(view=view, output_dir=tmp_path)
        controller.handle_interactive_download()
        assert any("cancelada" in m.lower() for m in view.messages_info)

    def test_handle_interactive_download_keyboard_interrupt_returns_cleanly(self, tmp_path: Path):
        """RF-03: Ctrl+C durante la descarga interactiva limpia y no propaga excepción."""
        view = FakeView(inputs=["youtube", "song query", "mp3"])
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube", side_effect=KeyboardInterrupt):
            controller.handle_interactive_download()
            assert any("cancelada por el usuario" in m.lower() for m in view.messages_warning)
            assert any("retornando al menú" in m.lower() for m in view.messages_info)

    def test_handle_interactive_download_empty_playlist(self, tmp_path: Path):
        """RF-07: Playlist vacía muestra aviso informativo y regresa sin error fatal."""
        view = FakeView(inputs=["youtube", "https://youtube.com/playlist?list=PL_empty", "mp3"])
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_playlist") as mock_pl:
            mock_pl.return_value = {
                "success": False,
                "error": "empty_playlist",
                "message": "Playlist vacía"
            }
            controller.handle_interactive_download()
            assert any("no contiene pistas descargables" in m.lower() for m in view.messages_info)

    def test_handle_interactive_download_ffmpeg_missing(self, tmp_path: Path):
        """RF-02: Error de FFmpeg faltante muestra advertencia/error descriptivo."""
        view = FakeView(inputs=["youtube", "song", "mp3"])
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube") as mock_down:
            mock_down.return_value = {
                "success": False,
                "error": "ffmpeg_missing",
                "message": "FFmpeg no encontrado"
            }
            controller.handle_interactive_download()
            assert any("ffmpeg" in m.lower() for m in view.messages_error)

    def test_handle_interactive_download_auto_adaptation(self, tmp_path: Path):
        """RF-07: Discrepancia entre plataforma elegida y URL dispara advertencia pedagógica."""
        # Eligió youtube pero ingresa link de youtube music
        view = FakeView(inputs=["youtube", "https://music.youtube.com/watch?v=123", "mp3"])
        controller = DownloadController(view=view, output_dir=tmp_path)

        with patch("controllers.download_controller.download_audio_from_youtube") as mock_down:
            mock_down.return_value = {
                "success": True,
                "title": "Music Track",
                "uploader": "Artist",
                "mp3_path": str(tmp_path / "track.mp3")
            }
            controller.handle_interactive_download()
            assert len(view.mismatches_shown) == 1
            assert view.mismatches_shown[0] == ("youtube", "youtube_music")
