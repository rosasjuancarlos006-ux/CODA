from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import flet as ft

from ui.gui.flet_view import FletView
from ui.view_interface import ViewInterface
from core.events import DownloadPhase, ProgressEvent


class MockPage:
    """Mock simplificado de ft.Page para pruebas unitarias sin dependencias externas."""
    def __init__(self):
        self.title: str = ""
        self.theme_mode: Optional[ft.ThemeMode] = None
        self.theme: Optional[ft.Theme] = None
        self.bgcolor: Optional[str] = None
        self.padding: Any = None
        self.window: Optional[ft.Window] = None
        self.controls: List[Any] = []
        self.dialogs: List[Any] = []
        self.overlay: List[Any] = []
        self.snack_bar: Optional[ft.SnackBar] = None

    def add(self, *controls):
        self.controls.extend(controls)

    def show_dialog(self, dialog):
        dialog.open = True
        self.dialogs.append(dialog)
        if isinstance(dialog, ft.SnackBar):
            self.snack_bar = dialog

    def pop_dialog(self):
        if self.dialogs:
            return self.dialogs.pop()
        return None

    def update(self):
        pass


def test_flet_view_implements_view_interface():
    view = FletView()
    assert isinstance(view, ViewInterface)


def test_flet_view_window_configuration():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    assert page.title == "CODA · Tu música, en tus archivos."
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.window is not None
    assert page.window.min_width == 800
    assert page.window.min_height == 600
    assert page.window.prevent_close is True
    assert len(page.controls) > 0


def test_flet_view_navigation_switches_sections():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    assert view.current_section == "inicio"

    view.navigate_to_section("descargas")
    assert view.current_section == "descargas"

    view.navigate_to_section("archivos")
    assert view.current_section == "archivos"

    view.navigate_to_section("inicio")
    assert view.current_section == "inicio"


def test_flet_view_show_toast():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    view.show_toast("Descarga iniciada con éxito")
    assert page.snack_bar is not None
    assert page.snack_bar.content.value == "Descarga iniciada con éxito"


def test_flet_view_show_modal_error_renders_dialog_and_buttons():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    clicked_action = []

    def on_btn_click(btn_label):
        clicked_action.append(btn_label)

    # Invocar modal de error con botones Reintentar y Aceptar / Volver
    chosen = view.show_modal_error(
        title="Error de conexión",
        message="No fue posible conectar con el servidor.",
        buttons=["Reintentar", "Aceptar / Volver al inicio"],
        on_action=on_btn_click,
    )

    assert chosen == "Reintentar"
    assert len(page.dialogs) == 1
    dialog = page.dialogs[0]
    assert isinstance(dialog, ft.AlertDialog)

    # Check alert icon, title and message
    assert dialog.title.value == "Error de conexión"
    assert dialog.content.value == "No fue posible conectar con el servidor."
    assert dialog.icon is not None
    assert len(dialog.actions) == 2

    # Click first button (Reintentar)
    dialog.actions[0].on_click(None)
    assert "Reintentar" in clicked_action


def test_flet_view_window_close_confirmation_when_downloads_active():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    # Mark active downloads
    view.has_active_download = True

    close_confirmed = []

    def on_confirm_close():
        close_confirmed.append(True)

    view.confirm_window_close(on_confirm=on_confirm_close)

    # Modal dialog should be shown
    assert len(page.dialogs) >= 1
    dialog = page.dialogs[-1]
    assert isinstance(dialog, ft.AlertDialog)
    assert "Descargas en curso" in dialog.title.value or "Cerrar" in dialog.title.value
    assert ("cancelarán" in dialog.content.value) or ("activas" in dialog.content.value)

    # Find the confirm exit button
    confirm_btn = None
    for act in dialog.actions:
        if "Cerrar" in getattr(act.content, "value", "") or "Salir" in getattr(act.content, "value", ""):
            confirm_btn = act

    assert confirm_btn is not None
    confirm_btn.on_click(None)
    assert len(close_confirmed) == 1


def test_flet_view_stubbed_contract_methods():
    view = FletView()
    page = MockPage()
    view.init_page(page)

    view.show_banner()
    assert view.show_main_menu() == "1"
    assert view.prompt_platform() in ("youtube", "youtube_music")
    assert view.prompt_query("youtube") == ""
    assert view.prompt_playlist_limit() is None
    assert view.prompt_audio_format(is_playlist=False) == "mp3"
    view.show_platform_mismatch("youtube", "youtube_music")
    view.show_info("Info")
    view.show_warning("Warning")
    view.show_error("Error")
    view.show_single_success({"title": "Test"})
    view.show_playlist_summary({"total": 1}, Path("downloads"))
    view.show_downloads_table([])
    view.show_empty_downloads()
    view.on_progress(ProgressEvent(phase=DownloadPhase.DOWNLOADING, percentage=50.0))
    view.start_progress_task("Task", 100)
    view.stop_progress_task()
    view.show_search_results([])
    view.show_queue_state([])
    assert view.show_modal_error("Error", "Mensaje", ["Aceptar"]) == "Aceptar"
