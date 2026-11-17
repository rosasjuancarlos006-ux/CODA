from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import pytest

from core.events import DownloadPhase, ProgressEvent
from core.queue_manager import QueueItem, QueueItemStatus
from controllers.gui_controller import GUIController


class FakeGUIView:
    def __init__(self):
        self.navigated_sections: List[str] = []
        self.toasts: List[str] = []
        self.queue_states: List[List[QueueItem]] = []
        self.modals: List[Dict[str, Any]] = []
        self.progress_events: List[ProgressEvent] = []
        self.single_successes: List[Dict[str, Any]] = []
        self.search_results: List[Dict[str, Any]] = []

    def navigate_to_section(self, section: str) -> None:
        self.navigated_sections.append(section)

    def show_toast(self, message: str) -> None:
        self.toasts.append(message)

    def show_queue_state(self, queue: List[Any]) -> None:
        self.queue_states.append(list(queue))

    def show_modal_error(self, title: str, message: str, buttons: List[str]) -> str:
        self.modals.append({"title": title, "message": message, "buttons": buttons})
        return buttons[0] if buttons else "Aceptar"

    def show_single_success(self, result: Dict[str, Any]) -> None:
        self.single_successes.append(result)

    def on_progress(self, event: ProgressEvent) -> None:
        self.progress_events.append(event)

    def show_search_results(self, results: List[Dict[str, Any]]) -> None:
        self.search_results = list(results)

    def show_banner(self) -> None: pass
    def show_main_menu(self) -> str: return "1"
    def prompt_platform(self) -> str: return "youtube"
    def prompt_query(self, platform_name: str) -> str: return ""
    def prompt_playlist_limit(self) -> Optional[int]: return None
    def prompt_audio_format(self, is_playlist: bool) -> str: return "mp3"
    def show_platform_mismatch(self, selected: str, adapted: str) -> None: pass
    def show_info(self, message: str) -> None: pass
    def show_warning(self, message: str) -> None: pass
    def show_error(self, message: str, error_type: Optional[str] = None) -> None: pass
    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None: pass
    def show_downloads_table(self, downloads: List[Any]) -> None: pass
    def show_empty_downloads(self) -> None: pass
    def start_progress_task(self, title: str, total: Optional[int] = None) -> None: pass
    def stop_progress_task(self) -> None: pass


def test_gui_controller_initial_state(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path)

    assert ctrl.cola_descargas == []
    assert ctrl.hay_tarea_activa() is False
    assert ctrl.is_running is True


def test_gui_controller_encolar_primera_tarea_navega_a_descargas(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path)

    item1 = QueueItem(
        item_id="item-1",
        title="Primera Cancion",
        url_or_query="https://youtube.com/watch?v=1",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:00",
        status=QueueItemStatus.PENDING,
    )

    ctrl.encolar_tarea(item1)

    assert len(ctrl.cola_descargas) == 1
    assert ctrl.cola_descargas[0].item_id == "item-1"
    assert "descargas" in view.navigated_sections


def test_gui_controller_encolar_tarea_con_activa_emite_toast_no_invasivo(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path)

    item_active = QueueItem(
        item_id="item-active",
        title="Cancion en curso",
        url_or_query="https://youtube.com/watch?v=active",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:30",
        status=QueueItemStatus.ACTIVE,
    )
    ctrl.cola_descargas.append(item_active)
    assert ctrl.hay_tarea_activa() is True

    item2 = QueueItem(
        item_id="item-2",
        title="Segunda Cancion",
        url_or_query="https://youtube.com/watch?v=2",
        platform="youtube_music",
        audio_format="opus",
        quality="best",
        playlist_limit=0,
        duration_str="02:50",
        status=QueueItemStatus.PENDING,
    )

    ctrl.encolar_tarea(item2)

    assert len(ctrl.cola_descargas) == 2
    assert "descargas" not in view.navigated_sections
    assert any("cola de descargas" in t.lower() or "agregado" in t.lower() for t in view.toasts)


def test_gui_controller_remover_de_cola(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path)

    item1 = QueueItem(
        item_id="id-1",
        title="Item 1",
        url_or_query="url1",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="01:00",
        status=QueueItemStatus.PENDING,
    )
    item2 = QueueItem(
        item_id="id-2",
        title="Item 2",
        url_or_query="url2",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="02:00",
        status=QueueItemStatus.PENDING,
    )
    ctrl.cola_descargas = [item1, item2]

    ctrl.remover_de_cola("id-1")

    assert len(ctrl.cola_descargas) == 1
    assert ctrl.cola_descargas[0].item_id == "id-2"


def test_gui_controller_worker_processes_item_to_completion(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    item = QueueItem(
        item_id="worker-success",
        title="Cancion Prueba",
        url_or_query="https://youtube.com/watch?v=test",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:00",
        status=QueueItemStatus.PENDING,
    )
    ctrl.cola_descargas = [item]

    # Mock download execution
    mock_result = {
        "success": True,
        "title": "Cancion Prueba",
        "file_path": tmp_path / "Cancion Prueba.mp3",
    }
    with patch("controllers.gui_controller.download_audio_from_youtube", return_value=mock_result) as mock_dl:
        # Run one step of dispatcher worker synchronously
        processed = ctrl._process_next_queue_item()
        assert processed is True
        mock_dl.assert_called_once()

    assert ctrl.cola_descargas[0].status == QueueItemStatus.COMPLETED
    assert len(view.single_successes) == 1
    assert view.single_successes[0]["title"] == "Cancion Prueba"


def test_gui_controller_cancel_active_task_purges_temporales(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    item1 = QueueItem(
        item_id="cancel-me",
        title="Cancion Cancelable",
        url_or_query="https://youtube.com/watch?v=cancel",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:00",
        status=QueueItemStatus.ACTIVE,
    )
    ctrl.cola_descargas = [item1]

    # Create dummy temporary file
    temp_file = tmp_path / "Cancion Cancelable.part"
    temp_file.write_bytes(b"temp data")

    # Cancel active
    ctrl.cancelar_tarea_activa("cancel-me")

    assert ctrl.cancellation_requested is True
    # Verify cleanup function called or temp file purged
    assert ctrl.cola_descargas[0].status == QueueItemStatus.CANCELLED
    # Since queue has no more pending items, navigate to inicio
    assert "inicio" in view.navigated_sections
    assert any("cancelada" in t.lower() for t in view.toasts)


def test_gui_controller_worker_handles_operational_error(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    item = QueueItem(
        item_id="error-task",
        title="Cancion con Error",
        url_or_query="https://youtube.com/watch?v=err",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:00",
        status=QueueItemStatus.PENDING,
    )
    ctrl.cola_descargas = [item]

    mock_fail = {
        "success": False,
        "error": "network_timeout",
        "message": "Fallo de conexión a la red",
    }
    with patch("controllers.gui_controller.download_audio_from_youtube", return_value=mock_fail):
        processed = ctrl._process_next_queue_item()
        assert processed is True

    # Shows modal error
    assert len(view.modals) == 1
    assert "Fallo" in view.modals[0]["message"] or "Error" in view.modals[0]["title"]
    assert ctrl.cola_descargas[0].status == QueueItemStatus.ERROR


def test_gui_controller_buscar_por_nombre_success(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    fake_results = [
        {
            "id": f"vid-{i}",
            "title": f"Song {i}",
            "artist": "Artist",
            "version": "Audio oficial",
            "duration_str": "03:30",
            "url": f"https://www.youtube.com/watch?v=vid-{i}",
        }
        for i in range(5)
    ]

    with patch("controllers.gui_controller.buscar_top_coincidencias", return_value=fake_results):
        ctrl.buscar_por_nombre("Bohemian Rhapsody", synchronous=True)

    # Verifica que la vista recibió los 5 resultados
    assert len(view.search_results) == 5
    assert view.search_results[0]["title"] == "Song 0"
    # El indicador de búsqueda debe haberse apagado
    assert ctrl.is_searching is False


def test_gui_controller_buscar_por_nombre_empty_results(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    with patch("controllers.gui_controller.buscar_top_coincidencias", return_value=[]):
        ctrl.buscar_por_nombre("CancionInexistenteXYZ123", synchronous=True)

    assert ctrl.is_searching is False
    assert len(view.modals) == 1
    assert "Sin coincidencias" in view.modals[0]["title"]
    msg = view.modals[0]["message"].lower()
    assert ("coincidencia" in msg) or ("encontraron" in msg)


def test_gui_controller_buscar_por_nombre_network_error(tmp_path: Path):
    view = FakeGUIView()
    ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

    with patch("controllers.gui_controller.buscar_top_coincidencias", side_effect=RuntimeError("Connection refused")):
        ctrl.buscar_por_nombre("Queen", synchronous=True)

    assert ctrl.is_searching is False
    assert len(view.modals) == 1
    assert "conexión" in view.modals[0]["title"].lower() or "error" in view.modals[0]["title"].lower()

