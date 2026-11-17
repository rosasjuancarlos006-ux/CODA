from pathlib import Path
import threading
import time
from unittest.mock import MagicMock, patch
import pytest

from controllers.gui_controller import GUIController
from core.queue_manager import QueueItem, QueueItemStatus
from ui.view_interface import ViewInterface


# =====================================================================
# QA Test Suite: Concurrencia de Cola FIFO y Worker Asíncrono (Tarea 3.2)
# =====================================================================


class DummyView(ViewInterface):
    """Implementación simulada y thread-safe de ViewInterface para pruebas de concurrencia."""

    def __init__(self):
        self.navigated_sections: list[str] = []
        self.toasts: list[str] = []
        self.queue_states: list[list[QueueItem]] = []
        self.errors: list[tuple[str, str]] = []
        self.successes: list[dict] = []
        self.progress_events: list = []
        self._lock = threading.Lock()

    def navigate_to_section(self, section: str) -> None:
        with self._lock:
            self.navigated_sections.append(section)

    def show_toast(self, message: str) -> None:
        with self._lock:
            self.toasts.append(message)

    def show_queue_state(self, queue: list) -> None:
        with self._lock:
            self.queue_states.append(list(queue))

    def show_modal_error(self, title: str, message: str, buttons=None, on_action=None) -> str:
        with self._lock:
            self.errors.append((title, message))
        return "Aceptar"

    def show_search_results(self, results: list) -> None:
        pass

    def show_banner(self) -> None:
        pass

    def show_main_menu(self) -> str:
        return "1"

    def prompt_platform(self) -> str:
        return "youtube"

    def prompt_query(self, platform_name: str) -> str:
        return ""

    def prompt_playlist_limit(self):
        return None

    def prompt_audio_format(self, is_playlist: bool) -> str:
        return "mp3"

    def show_platform_mismatch(self, selected: str, adapted: str) -> None:
        pass

    def show_info(self, message: str) -> None:
        pass

    def show_warning(self, message: str) -> None:
        pass

    def show_error(self, message: str, error_type=None) -> None:
        pass

    def show_single_success(self, result: dict) -> None:
        with self._lock:
            self.successes.append(dict(result))

    def show_playlist_summary(self, summary: dict, output_dir: Path) -> None:
        pass

    def show_downloads_table(self, downloads: list) -> None:
        pass

    def show_empty_downloads(self) -> None:
        pass

    def on_progress(self, event) -> None:
        with self._lock:
            self.progress_events.append(event)

    def start_progress_task(self, title: str, total=None) -> None:
        pass

    def stop_progress_task(self) -> None:
        pass


class TestGUIQueueConcurrencyQA:
    """
    Pruebas rigurosas de sincronización multihilo, cola FIFO,
    despacho secuencial y remoción segura de tareas pendientes.
    """

    def _sample_item(self, item_id: str, title: str = "Pista") -> QueueItem:
        return QueueItem(
            item_id=item_id,
            title=title,
            url_or_query=f"https://www.youtube.com/watch?v={item_id}",
            platform="youtube",
            audio_format="mp3",
            quality="best",
            playlist_limit=0,
            duration_str="03:00",
            status=QueueItemStatus.PENDING,
        )

    def test_tc_3_2_1_sequential_processing_fifo(self, tmp_path: Path):
        """
        Verifica el procesamiento estrictamente secuencial de múltiples pistas
        encoladas en el despachador secundario: nunca dos tareas en estado ACTIVE simultáneamente.
        """
        view = DummyView()
        ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

        item1 = self._sample_item("item-1", "Canción 1")
        item2 = self._sample_item("item-2", "Canción 2")

        ctrl.encolar_tarea(item1)
        ctrl.encolar_tarea(item2)

        # Mock de descarga rápida
        with patch("controllers.gui_controller.download_audio_from_youtube") as mock_dl:
            mock_dl.return_value = {"success": True, "title": "Descargada"}

            # Procesar el primer ítem
            processed1 = ctrl._process_next_queue_item()
            assert processed1 is True
            assert ctrl.cola_descargas[0].status == QueueItemStatus.COMPLETED
            assert ctrl.cola_descargas[1].status == QueueItemStatus.PENDING

            # Procesar el segundo ítem
            processed2 = ctrl._process_next_queue_item()
            assert processed2 is True
            assert ctrl.cola_descargas[1].status == QueueItemStatus.COMPLETED

            # La cola ahora no tiene pendientes
            processed3 = ctrl._process_next_queue_item()
            assert processed3 is False

    def test_tc_3_2_2_navigation_vs_toast_on_enqueue(self, tmp_path: Path):
        """
        Regla de navegación al encolar:
        - Si no hay descargas previas activas: navega de inmediato a 'descargas'.
        - Si ya existe una descarga en curso: no interrumpe la navegación y emite toast.
        """
        view = DummyView()
        ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

        item1 = self._sample_item("item-1", "Pista 1")
        item2 = self._sample_item("item-2", "Pista 2")

        # 1. Encolar primera tarea (sin activa previa)
        ctrl.encolar_tarea(item1)
        assert "descargas" in view.navigated_sections
        assert len(view.toasts) == 0

        # Simular que item1 pasa a ACTIVE
        from core.queue_manager import update_item_status
        ctrl.cola_descargas = update_item_status(ctrl.cola_descargas, "item-1", QueueItemStatus.ACTIVE)
        assert ctrl.hay_tarea_activa() is True

        # 2. Encolar segunda tarea mientras hay una activa
        ctrl.encolar_tarea(item2)
        assert len(view.navigated_sections) == 1  # No volvió a redirigir
        assert len(view.toasts) >= 1
        assert "agregado a la cola" in view.toasts[-1]

    def test_tc_3_2_3_remove_pending_does_not_affect_active(self, tmp_path: Path):
        """
        Remover de la cola elimina únicamente tareas PENDING sin alterar la tarea ACTIVE.
        """
        view = DummyView()
        ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

        item_active = self._sample_item("id-active", "Activa")
        item_pending = self._sample_item("id-pending", "Pendiente")

        ctrl.encolar_tarea(item_active)
        ctrl.encolar_tarea(item_pending)

        # Poner item_active en estado ACTIVE
        from core.queue_manager import update_item_status
        ctrl.cola_descargas = update_item_status(ctrl.cola_descargas, "id-active", QueueItemStatus.ACTIVE)

        # Remover tarea activa -> NO debe removerse
        ctrl.remover_de_cola("id-active")
        ids = [i.item_id for i in ctrl.cola_descargas]
        assert "id-active" in ids

        # Remover tarea pendiente -> DEBE removerse
        ctrl.remover_de_cola("id-pending")
        ids_after = [i.item_id for i in ctrl.cola_descargas]
        assert "id-pending" not in ids_after
        assert "id-active" in ids_after

    def test_tc_3_2_4_concurrent_enqueue_thread_safety(self, tmp_path: Path):
        """
        Prueba de concurrencia bajo múltiples hilos agregando tareas simultáneamente:
        garantiza que _lock proteja la integridad de la cola sin excepciones de carrera.
        """
        view = DummyView()
        ctrl = GUIController(view=view, output_dir=tmp_path, autostart_worker=False)

        num_threads = 10
        items_per_thread = 5

        def worker_enqueue(worker_idx: int):
            for i in range(items_per_thread):
                item = self._sample_item(f"w{worker_idx}-item{i}", f"Worker {worker_idx} - {i}")
                ctrl.encolar_tarea(item)

        threads = [
            threading.Thread(target=worker_enqueue, args=(w,))
            for w in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert len(ctrl.cola_descargas) == num_threads * items_per_thread
        ids = [i.item_id for i in ctrl.cola_descargas]
        assert len(set(ids)) == num_threads * items_per_thread
