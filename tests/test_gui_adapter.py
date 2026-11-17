import inspect
from pathlib import Path
from typing import Any, Dict, List
import pytest

from core.events import DownloadPhase, ProgressEvent, create_progress_event
from core.queue_manager import QueueItem, QueueItemStatus
from ui.gui.flet_view import FletView
from ui.view_interface import ViewInterface


def test_flet_view_implements_view_interface():
    """
    1) Validación estructural de que FletView satisface el contrato ViewInterface
    según el protocolo @runtime_checkable de Python.
    """
    view = FletView()
    assert isinstance(view, ViewInterface), "FletView debe implementar ViewInterface"

    # Verificar que todos los métodos requeridos del protocolo existen y son invocables
    required_methods = [
        "show_banner",
        "show_main_menu",
        "prompt_platform",
        "prompt_query",
        "prompt_playlist_limit",
        "prompt_audio_format",
        "show_platform_mismatch",
        "show_info",
        "show_warning",
        "show_error",
        "show_single_success",
        "show_playlist_summary",
        "show_downloads_table",
        "show_empty_downloads",
        "on_progress",
        "start_progress_task",
        "stop_progress_task",
        "show_search_results",
        "show_queue_state",
        "show_toast",
        "show_modal_error",
        "navigate_to_section",
    ]

    for method_name in required_methods:
        method = getattr(view, method_name, None)
        assert method is not None, f"FletView carece del método requerido: {method_name}"
        assert callable(method), f"{method_name} debe ser un método invocable"


def test_gui_event_consumption_in_memory():
    """
    2) Emisión de eventos ProgressEvent y actualización del estado de cola a la vista
    simulada en memoria, verificando la reactividad interna sin bucle visual ni ventana física.
    """
    view = FletView()
    assert view.active_progress is None
    assert view.has_active_download is False
    assert view.queue_items == []

    # Emitir evento de progreso usando create_progress_event
    evt = create_progress_event(
        phase=DownloadPhase.DOWNLOADING,
        percentage=45.5,
        speed_bytes_sec=3200000.0,
        eta_seconds=15,
        item_title="Canción de Prueba",
        message="Descargando audio",
    )
    view.on_progress(evt)

    assert view.active_progress is not None
    assert view.active_progress.percentage == 45.5
    assert view.active_progress.phase == DownloadPhase.DOWNLOADING
    assert view.active_progress.speed_bytes_sec == 3200000.0

    # Actualizar estado de cola con un elemento ACTIVE
    item_active = QueueItem(
        item_id="task-1",
        title="Canción de Prueba",
        url_or_query="https://youtube.com/watch?v=123",
        platform="youtube",
        audio_format="mp3",
        quality="auto",
        playlist_limit=0,
        duration_str="03:45",
        status=QueueItemStatus.ACTIVE,
    )
    view.show_queue_state([item_active])

    assert len(view.queue_items) == 1
    assert view.has_active_download is True

    # Navegación entre secciones en memoria
    view.navigate_to_section("descargas")
    assert view.current_section == "descargas"
    view.navigate_to_section("archivos")
    assert view.current_section == "archivos"
    view.navigate_to_section("inicio")
    assert view.current_section == "inicio"


def test_spanish_text_enforcement_in_gui_strings():
    """
    3) Inspección de archivos fuente y literales en ui/gui/ confirmando la ausencia
    de mensajes y textos en inglés destinados al usuario final (estrictamente en español).
    """
    gui_dir = Path(__file__).resolve().parent.parent / "ui" / "gui"
    assert gui_dir.exists(), f"Directorio {gui_dir} no encontrado"

    py_files = list(gui_dir.rglob("*.py"))
    assert len(py_files) >= 5, "Deben existir los módulos base de la GUI"

    # Términos en inglés típicos de interfaz que estarían prohibidos en la UI hacia el usuario
    prohibited_ui_tokens = [
        '"Download music"',
        '"Search by name"',
        '"Paste link"',
        '"Queue"',
        '"Downloads"',
        '"Settings"',
        '"Cancel download"',
        '"Retry"',
        '"Downloaded files"',
        '"Open folder"',
    ]

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for token in prohibited_ui_tokens:
            assert token.lower() not in content.lower(), (
                f"Término en inglés '{token}' detectado en archivo de GUI: {py_file.name}. "
                "La interfaz debe estar 100% en español."
            )
