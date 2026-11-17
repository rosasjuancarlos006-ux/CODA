import time
from unittest.mock import MagicMock
import pytest

from core.events import DownloadPhase, ProgressEvent
from ui.gui.flet_view import FletView


# =====================================================================
# QA Test Suite: Throttling de Progreso y Thread-Safety UI (Tarea 3.3)
# =====================================================================


class TestUIProgressThrottlingQA:
    """
    Pruebas de estrés y rendimiento de UI:
    Verifica que llamadas de alta frecuencia a on_progress no saturen el IPC
    ni disparen reconstrucciones masivas y que capturen errores en desconexión.
    """

    def test_tc_3_3_1_progress_throttling_high_frequency(self):
        """
        Simula una emisión de progreso a 100 Hz (100 eventos en 100 ms).
        Verifica que el mecanismo de throttle limite las actualizaciones pesadas
        del contenedor central sin perder las transiciones clave de fase (COMPLETED, ERROR).
        """
        view = FletView()
        view.current_section = "descargas"
        view._content_container = MagicMock()
        mock_safe_update = MagicMock()
        view._safe_update = mock_safe_update

        # Emitir 100 eventos de descarga en rápida sucesión
        start_time = time.time()
        for i in range(100):
            evt = ProgressEvent(
                phase=DownloadPhase.DOWNLOADING,
                percentage=float(i),
                speed_bytes_sec=1024.0 * (i + 1),
                eta_seconds=100 - i,
            )
            view.on_progress(evt)

        # Enviar evento de finalización (mandatorio que se procese de inmediato)
        final_evt = ProgressEvent(
            phase=DownloadPhase.COMPLETED,
            percentage=100.0,
            message="Completado",
        )
        view.on_progress(final_evt)

        # Con throttle, el número de actualizaciones de la UI pesada no debe ser 101
        # Debe haber reducido significativamente la frecuencia de reconstrucción
        assert mock_safe_update.call_count < 30, (
            f"Fallo de saturación IPC: _safe_update fue llamado {mock_safe_update.call_count} veces "
            f"para 101 eventos en ráfaga."
        )

        # El último progreso almacenado debe ser el evento final
        assert view.active_progress == final_evt

    def test_tc_3_3_2_safe_update_catches_runtime_and_session_errors(self):
        """
        Verifica que _safe_update no propague excepciones cuando Flet arroje
        RuntimeError (control no montado) o Exception genérica por sesión desconectada.
        """
        view = FletView()
        mock_page = MagicMock()
        mock_page.update.side_effect = RuntimeError("Control must be added to page first.")
        view.page = mock_page

        mock_control = MagicMock()
        mock_control.update.side_effect = RuntimeError("Control disconnected")

        # No debe lanzar ninguna excepción
        try:
            view._safe_update(mock_control)
            view._safe_update(None)
        except Exception as exc:
            pytest.fail(f"_safe_update propagó una excepción inesperada: {exc}")
