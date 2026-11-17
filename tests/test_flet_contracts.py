from pathlib import Path
from unittest.mock import MagicMock
import pytest
import flet as ft

from core.queue_manager import QueueItem, QueueItemStatus
from ui.gui.flet_view import FletView
from ui.gui.views.options_view import build_options_view


# =====================================================================
# QA Test Suite: Contratos de Datos OptionsView -> FletView (Tarea 3.1)
# =====================================================================


def _find_control_by_key_or_data(control: ft.Control, key_or_data: str):
    """Buscador recursivo de controles Flet por key (flet[test]) o atributo data."""
    if getattr(control, "key", None) == key_or_data or getattr(control, "data", None) == key_or_data:
        return control

    # Si tiene atributo controls (Column, Row, Stack, etc.)
    if hasattr(control, "controls") and isinstance(control.controls, list):
        for child in control.controls:
            found = _find_control_by_key_or_data(child, key_or_data)
            if found:
                return found

    # Si tiene atributo content (Container, etc.)
    if hasattr(control, "content") and control.content:
        found = _find_control_by_key_or_data(control.content, key_or_data)
        if found:
            return found

    return None


class TestFletContractsQA:
    """
    Pruebas rigurosas del contrato de datos entre OptionsView, FletView y GUIController.
    Verifica que bajo ningún concepto se encolen QueueItems con url_or_query="",
    title="Canción seleccionada" o audio_format erróneo.
    """

    def test_tc_3_1_1_options_view_to_flet_view_contract_integrity(self):
        """
        Verifica que el payload emitido por OptionsView al confirmar la descarga
        sea interpretado correctamente por FletView._handle_start_download_from_options
        sin perder la URL, título, formato ni plataforma.
        """
        view = FletView()
        mock_controller = MagicMock()
        view.set_controller(mock_controller)

        # 1. Simular opciones emitidas por OptionsView (payload plano según options_view.py)
        chosen_options_flat = {
            "title": "Rosalía - DESPECHÁ",
            "artist": "Rosalía",
            "duration_str": "02:37",
            "url": "https://www.youtube.com/watch?v=o2d5e_n7bZ4",
            "is_playlist": False,
            "platform": "youtube_music",
            "audio_format": "m4a",
            "quality": "best",
            "playlist_limit": None,
        }

        # Ejecutar el handler de encolado
        view._handle_start_download_from_options(chosen_options_flat)

        # Verificar que el controlador haya recibido la tarea
        assert mock_controller.encolar_tarea.called
        queued_item: QueueItem = mock_controller.encolar_tarea.call_args[0][0]

        # Aserciones mandatorias para evitar la causa raíz del fallo en Flet
        assert queued_item.url_or_query == "https://www.youtube.com/watch?v=o2d5e_n7bZ4", (
            f"Error crítico de contrato: url_or_query quedó vacía: '{queued_item.url_or_query}'"
        )
        assert queued_item.title == "Rosalía - DESPECHÁ"
        assert queued_item.audio_format == "m4a"
        assert queued_item.platform == "youtube_music"
        assert queued_item.duration_str == "02:37"
        assert queued_item.status == QueueItemStatus.PENDING

    def test_tc_3_1_2_search_flow_to_options_to_queue(self):
        """
        Simula el flujo completo desde selección en búsqueda hasta encolado:
        SearchView track -> FletView._handle_select_track_from_search -> OptionsView -> QueueItem.
        Localiza controles mediante keys nativas compatibles con flet[test].
        """
        view = FletView()
        mock_controller = MagicMock()
        view.set_controller(mock_controller)

        # Pista seleccionada en SearchView
        search_track = {
            "id": "abc123vid",
            "title": "Camilo - Una Vida Pasada",
            "artist": "Camilo, Carín León",
            "channel": "Camilo",
            "duration_str": "03:45",
            "duration": 225,
            "url": "https://music.youtube.com/watch?v=hrcBnDALOQs",
        }

        view._handle_select_track_from_search(search_track)
        assert view.current_section == "opciones"
        assert view.selected_track_for_options is not None
        assert view.selected_track_for_options["url"] == "https://music.youtube.com/watch?v=hrcBnDALOQs"

        # Simular que el usuario pulsa 'Iniciar descarga' en OptionsView
        options_container = build_options_view(
            track_info=view.selected_track_for_options,
            on_start_download=view._handle_start_download_from_options,
        )

        # Buscar mediante key formal compatible con flet.testing.Tester ("options_start_download_btn")
        start_btn = _find_control_by_key_or_data(options_container, "options_start_download_btn")
        assert start_btn is not None
        assert getattr(start_btn, "key", None) == "options_start_download_btn"
        assert callable(start_btn.on_click)

        # Disparar click en start_btn
        start_btn.on_click(None)

        assert mock_controller.encolar_tarea.called
        item: QueueItem = mock_controller.encolar_tarea.call_args[0][0]
        assert item.url_or_query == "https://music.youtube.com/watch?v=hrcBnDALOQs"
        assert item.title == "Camilo - Una Vida Pasada"
        assert item.audio_format == "mp3"  # formato por defecto

    def test_tc_3_1_3_paste_url_flow_to_options_to_queue(self):
        """
        Simula el flujo desde pegado/análisis en Inicio hasta encolado:
        HomeView -> FletView._handle_analyze_url -> OptionsView -> QueueItem.
        """
        view = FletView()
        mock_controller = MagicMock()
        view.set_controller(mock_controller)

        valid_url = "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
        view._handle_analyze_url(valid_url)

        assert view.current_section == "opciones"
        assert view.selected_track_for_options is not None
        assert view.selected_track_for_options["url"] == valid_url
        assert view.selected_track_for_options["is_playlist"] is True

        # Simular confirmación desde OptionsView
        options_container = build_options_view(
            track_info=view.selected_track_for_options,
            on_start_download=view._handle_start_download_from_options,
        )
        start_btn = _find_control_by_key_or_data(options_container, "options_start_download_btn")
        assert start_btn is not None
        assert callable(start_btn.on_click)
        start_btn.on_click(None)

        assert mock_controller.encolar_tarea.called
        item: QueueItem = mock_controller.encolar_tarea.call_args[0][0]
        assert item.url_or_query == valid_url
        assert item.title == "Lista de reproducción"
        assert item.audio_format == "mp3"

    def test_tc_3_1_4_cancel_button_navigates_to_home(self):
        """Verifica que el botón cancelar en OptionsView posea key y callback hacia inicio."""
        cancel_called = False

        def on_cancel():
            nonlocal cancel_called
            cancel_called = True

        options_container = build_options_view(
            track_info={"title": "Cancion"},
            on_cancel=on_cancel,
        )
        cancel_btn = _find_control_by_key_or_data(options_container, "options_cancel_btn")
        assert cancel_btn is not None
        assert getattr(cancel_btn, "key", None) == "options_cancel_btn"
        cancel_btn.on_click(None)
        assert cancel_called is True
