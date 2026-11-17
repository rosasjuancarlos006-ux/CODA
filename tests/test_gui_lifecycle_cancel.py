import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from controllers.gui_controller import GUIController
from core.events import DownloadPhase, ProgressEvent
from core.queue_manager import QueueItem, QueueItemStatus
from ui.gui.flet_view import FletView


class TestGUILifecycleCancelQA:
    """
    Suite QA para Tarea 3.4:
    Ciclo de vida: Cancelación activa con purga de temporales, modales de error pedagógico
    y confirmación de cierre de ventana (prevent_close).
    """

    def _create_dummy_queue_item(
        self,
        item_id: str,
        title: str,
        url_or_query: str,
        status: QueueItemStatus = QueueItemStatus.PENDING,
    ) -> QueueItem:
        return QueueItem(
            item_id=item_id,
            title=title,
            url_or_query=url_or_query,
            platform="youtube",
            audio_format="mp3",
            quality="192",
            playlist_limit=10,
            duration_str="03:30",
            status=status,
        )

    def test_tc_3_4_1_cancel_active_task_purges_temp_files_and_advances_queue(self, tmp_path):
        """
        TC-3.4.1: Cancelación de tarea activa (cancelar_tarea_activa):
        El worker/controlador interrumpe la descarga activa, purga los temporales (.part, .ytdl),
        marca la tarea como CANCELLED y avanza a la siguiente tarea pendiente en cola.
        """
        # Crear archivos temporales simulando una descarga en proceso
        temp_part = tmp_path / "song1.mp3.part"
        temp_ytdl = tmp_path / "song1.ytdl"
        temp_part.write_bytes(b"partial content")
        temp_ytdl.write_bytes(b"metadata ytdl")

        mock_view = MagicMock()
        controller = GUIController(view=mock_view, output_dir=tmp_path)

        # Encolar dos ítems
        item1 = self._create_dummy_queue_item("task_1", "Cancion 1", "https://youtube.com/watch?v=111", QueueItemStatus.ACTIVE)
        item2 = self._create_dummy_queue_item("task_2", "Cancion 2", "https://youtube.com/watch?v=222", QueueItemStatus.PENDING)

        with controller._lock:
            controller.cola_descargas = [item1, item2]
            controller._active_item_id = "task_1"

        # Cancelar tarea activa
        controller.cancelar_tarea_activa("task_1")

        # 1. Comprobar que los archivos temporales fueron eliminados
        assert not temp_part.exists()
        assert not temp_ytdl.exists()

        # 2. Comprobar estado de la cola: task_1 CANCELLED, task_2 PENDING
        assert controller.cancellation_requested is True
        task1_item = next(i for i in controller.cola_descargas if i.item_id == "task_1")
        task2_item = next(i for i in controller.cola_descargas if i.item_id == "task_2")
        assert task1_item.status == QueueItemStatus.CANCELLED
        assert task2_item.status == QueueItemStatus.PENDING

        # 3. Al quedar pendientes, debió emitir toast indicando avance a la siguiente pista
        mock_view.show_toast.assert_called_with("Descarga cancelada. Iniciando siguiente pista.")

    def test_tc_3_4_1_cancel_active_task_last_item_navigates_home(self, tmp_path):
        """
        TC-3.4.1 (Variante sin pendientes): Si no quedan ítems pendientes,
        tras cancelar se redirige la vista a la sección 'inicio'.
        """
        mock_view = MagicMock()
        controller = GUIController(view=mock_view, output_dir=tmp_path)

        item = self._create_dummy_queue_item("solo_task", "Solo Track", "https://youtube.com/watch?v=solo", QueueItemStatus.ACTIVE)
        with controller._lock:
            controller.cola_descargas = [item]
            controller._active_item_id = "solo_task"

        controller.cancelar_tarea_activa("solo_task")

        assert controller.cancellation_requested is True
        mock_view.show_toast.assert_called_with("Descarga cancelada.")
        mock_view.navigate_to_section.assert_called_with("inicio")

    def test_tc_3_4_2_show_modal_error_dialog_and_action_dispatch(self):
        """
        TC-3.4.2: Despliegue de modal de error pedagógico ante fallos,
        permitiendo interactuar con los botones de acción («Reintentar» / «Aceptar / Volver al inicio»).
        """
        view = FletView()
        mock_page = MagicMock()
        view.page = mock_page

        action_received = []

        def on_modal_action(btn_label: str):
            action_received.append(btn_label)

        # Invocar show_modal_error
        view.show_modal_error(
            title="Error de conexión",
            message="No fue posible conectar con el servidor.",
            buttons=["Reintentar", "Aceptar / Volver al inicio"],
            on_action=on_modal_action,
        )

        # Verificar que se presentó el diálogo en la página
        assert mock_page.show_dialog.called
        dialog = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dialog, ft.AlertDialog)
        assert dialog.title.value == "Error de conexión"
        assert "No fue posible conectar" in dialog.content.value
        assert len(dialog.actions) == 2

        # Comprobar keys de botones para flet[test]
        btn_retry = dialog.actions[0]
        btn_accept = dialog.actions[1]
        assert btn_retry.key == "error_modal_btn_reintentar"
        assert btn_accept.key == "error_modal_btn_aceptar___volver_al_inicio"

        # Simular clic en 'Reintentar'
        btn_retry.on_click(None)
        assert action_received == ["Reintentar"]
        assert dialog.open is False

    def test_tc_3_4_3_prevent_close_window_interception_with_active_downloads(self):
        """
        TC-3.4.3: Confirmación de cierre de ventana (prevent_close):
        Si hay descargas activas, interceptar el evento 'close', abrir diálogo de confirmación.
        Si el usuario cancela, no cerrar; si el usuario confirma salida, cerrar ventana.
        """
        view = FletView()
        mock_page = MagicMock()
        mock_window = MagicMock()
        mock_window.prevent_close = True
        mock_page.window = mock_window
        view.page = mock_page

        # Simular descarga activa
        view.has_active_download = True

        # Interceptar evento close
        mock_event = MagicMock()
        mock_event.type = "close"
        mock_event.data = "close"
        view._handle_window_event(mock_event)

        # Verificar que se abrió el diálogo de confirmación de cierre
        assert mock_page.show_dialog.called
        dialog = mock_page.show_dialog.call_args[0][0]
        assert isinstance(dialog, ft.AlertDialog)
        assert dialog.title.value == "Descargas en curso"
        assert len(dialog.actions) == 2

        btn_cancel_close = dialog.actions[0]
        btn_confirm_close = dialog.actions[1]
        assert btn_cancel_close.key == "close_dialog_cancel_btn"
        assert btn_confirm_close.key == "close_dialog_confirm_btn"

        # 1. Simular clic en "Continuar descargando" (Cancelar salida)
        btn_cancel_close.on_click(None)
        assert dialog.open is False
        assert mock_window.destroy.called is False

        # 2. Simular clic en "Cerrar y salir" (Confirmar salida forzada)
        btn_confirm_close.on_click(None)
        assert mock_window.prevent_close is False
        assert mock_window.destroy.called is True

    def test_tc_3_4_3_prevent_close_window_direct_close_when_idle(self):
        """
        TC-3.4.3 (Variante idle): Si NO hay descargas activas,
        el cierre de ventana procede inmediatamente sin desplegar diálogo.
        """
        view = FletView()
        mock_page = MagicMock()
        mock_window = MagicMock()
        mock_page.window = mock_window
        view.page = mock_page

        view.has_active_download = False

        mock_event = MagicMock()
        mock_event.type = "close"
        mock_event.data = "close"
        view._handle_window_event(mock_event)

        assert mock_page.show_dialog.called is False
        assert mock_window.prevent_close is False
        assert mock_window.destroy.called is True
