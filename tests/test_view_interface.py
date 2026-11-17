from pathlib import Path
from typing import Optional, List, Dict, Any
import pytest
from core.events import ProgressEvent, DownloadPhase
from utils.file_manager import AudioFileInfo
from ui.view_interface import ViewInterface


class DummyCompleteView:
    """Implementación de prueba que satisface todos los métodos de ViewInterface."""
    def show_banner(self) -> None: pass
    def show_main_menu(self) -> str: return "1"
    def prompt_platform(self) -> str: return "youtube"
    def prompt_query(self, platform_name: str) -> str: return "query"
    def prompt_playlist_limit(self) -> Optional[int]: return 5
    def prompt_audio_format(self, is_playlist: bool) -> str: return "mp3"
    def show_platform_mismatch(self, selected: str, adapted: str) -> None: pass
    def show_info(self, message: str) -> None: pass
    def show_warning(self, message: str) -> None: pass
    def show_error(self, message: str, error_type: Optional[str] = None) -> None: pass
    def show_single_success(self, result: Dict[str, Any]) -> None: pass
    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None: pass
    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None: pass
    def show_empty_downloads(self) -> None: pass
    def on_progress(self, event: ProgressEvent) -> None: pass
    def start_progress_task(self, title: str, total: Optional[int] = None) -> None: pass
    def stop_progress_task(self) -> None: pass
    # Métodos ampliados para soporte GUI (Tarea 8)
    def show_search_results(self, results: List[Dict[str, Any]]) -> None: pass
    def show_queue_state(self, queue: List[Any]) -> None: pass
    def show_toast(self, message: str) -> None: pass
    def show_modal_error(self, title: str, message: str, buttons: List[str]) -> str: return "Reintentar"
    def navigate_to_section(self, section: str) -> None: pass


class DummyIncompleteView:
    """Implementación incompleta para verificar que el protocolo rechace clases no conformes."""
    def show_banner(self) -> None: pass


class TestViewInterface:
    def test_protocol_conformance_with_complete_view(self):
        view = DummyCompleteView()
        assert isinstance(view, ViewInterface)

    def test_protocol_rejection_with_incomplete_view(self):
        incomplete = DummyIncompleteView()
        assert not isinstance(incomplete, ViewInterface)

    def test_protocol_method_signatures(self):
        expected_methods = {
            "show_banner", "show_main_menu", "prompt_platform", "prompt_query",
            "prompt_playlist_limit", "prompt_audio_format", "show_platform_mismatch",
            "show_info", "show_warning", "show_error", "show_single_success",
            "show_playlist_summary", "show_downloads_table", "show_empty_downloads",
            "on_progress", "start_progress_task", "stop_progress_task",
            # Nuevos métodos de la GUI
            "show_search_results", "show_queue_state", "show_toast",
            "show_modal_error", "navigate_to_section"
        }
        protocol_methods = {m for m in dir(ViewInterface) if not m.startswith("_")}
        assert expected_methods.issubset(protocol_methods)
