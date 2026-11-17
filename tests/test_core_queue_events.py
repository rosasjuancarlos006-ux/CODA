import pytest
from dataclasses import FrozenInstanceError

from core.events import DownloadPhase, ProgressEvent, create_progress_event
from core.queue_manager import (
    QueueItem,
    QueueItemStatus,
    add_to_queue,
    get_next_pending_item,
    remove_from_queue,
    update_item_status,
)


# =====================================================================
# QA Test Suite: Modelo de Eventos y Cola FIFO Pura (Tarea 1.2)
# =====================================================================


class TestEventsCoreQA:
    """Pruebas exhaustivas para DownloadPhase, ProgressEvent y create_progress_event."""

    def test_tc_1_2_1_download_phase_taxonomy(self):
        """Verifica la taxonomía canónica completa de fases de descarga."""
        phases = {p.value for p in DownloadPhase}
        expected = {"preparing", "downloading", "converting", "metadata", "completed", "error"}
        assert phases == expected
        assert len(DownloadPhase) == 6

    def test_tc_1_2_1_progress_event_immutability(self):
        """Asegura la inmutabilidad física del DTO de progreso (FrozenInstanceError)."""
        event = ProgressEvent(
            phase=DownloadPhase.DOWNLOADING,
            percentage=45.5,
            speed_bytes_sec=1048576.0,
            eta_seconds=12,
            current_item=1,
            total_items=5,
            item_title="Test Track",
            message="Descargando...",
        )
        assert event.phase == DownloadPhase.DOWNLOADING
        assert event.percentage == 45.5

        with pytest.raises(FrozenInstanceError):
            event.percentage = 90.0  # type: ignore

        with pytest.raises(FrozenInstanceError):
            event.phase = DownloadPhase.COMPLETED  # type: ignore

    def test_tc_1_2_1_create_progress_event_clamping_and_types(self):
        """Verifica el clamping matemático [0.0, 100.0] y conversión limpia de tipos."""
        # Clamping superior
        event_over = create_progress_event(DownloadPhase.DOWNLOADING, percentage=150.0)
        assert event_over.percentage == 100.0

        # Clamping inferior
        event_under = create_progress_event(DownloadPhase.DOWNLOADING, percentage=-25.0)
        assert event_under.percentage == 0.0

        # Porcentaje None permitido
        event_none = create_progress_event(DownloadPhase.PREPARING, percentage=None)
        assert event_none.percentage is None

        # Conversiones de tipo seguras
        event_types = create_progress_event(
            phase=DownloadPhase.DOWNLOADING,
            percentage="75.2",  # type: ignore
            speed_bytes_sec="2048",  # type: ignore
            eta_seconds="15",  # type: ignore
            current_item="2",  # type: ignore
            total_items="10",  # type: ignore
            item_title=12345,  # type: ignore
            message=["Ok"],  # type: ignore
        )
        assert event_types.percentage == 75.2
        assert event_types.speed_bytes_sec == 2048.0
        assert event_types.eta_seconds == 15
        assert event_types.current_item == 2
        assert event_types.total_items == 10
        assert event_types.item_title == "12345"
        assert event_types.message == "['Ok']"


class TestQueueManagerCoreQA:
    """Pruebas exhaustivas para QueueItem, estados y operaciones funcionales FIFO puras."""

    def _sample_item(
        self,
        item_id: str = "item-1",
        title: str = "Cancion",
        status: QueueItemStatus = QueueItemStatus.PENDING,
    ) -> QueueItem:
        return QueueItem(
            item_id=item_id,
            title=title,
            url_or_query=f"https://www.youtube.com/watch?v={item_id}",
            platform="youtube",
            audio_format="mp3",
            quality="best",
            playlist_limit=0,
            duration_str="03:30",
            status=status,
        )

    def test_tc_1_2_2_queue_item_immutability_and_defaults(self):
        """Verifica la inmutabilidad y valores por defecto del QueueItem."""
        item = self._sample_item()
        assert item.status == QueueItemStatus.PENDING
        assert item.error_message is None
        assert item.thumbnail_url is None

        with pytest.raises(FrozenInstanceError):
            item.status = QueueItemStatus.ACTIVE  # type: ignore

        with pytest.raises(FrozenInstanceError):
            item.title = "Nuevo Titulo"  # type: ignore

    def test_tc_1_2_3_add_to_queue_pure_and_fifo_order(self):
        """add_to_queue agrega al final preservando orden FIFO y pureza funcional."""
        q0: list[QueueItem] = []
        item1 = self._sample_item(item_id="id-1", title="Cancion 1")
        item2 = self._sample_item(item_id="id-2", title="Cancion 2")

        q1 = add_to_queue(q0, item1)
        assert len(q1) == 1
        assert len(q0) == 0  # Inmutabilidad de la lista origen

        q2 = add_to_queue(q1, item2)
        assert len(q2) == 2
        assert q2[0].item_id == "id-1"
        assert q2[1].item_id == "id-2"

        # Rechazo de IDs duplicados
        with pytest.raises(ValueError, match="already exists"):
            duplicate_item = self._sample_item(item_id="id-1", title="Duplicado")
            add_to_queue(q2, duplicate_item)

    def test_tc_1_2_3_remove_from_queue_rules(self):
        """remove_from_queue solo elimina ítems PENDING; preserva ACTIVE."""
        item1 = self._sample_item("id-1", status=QueueItemStatus.ACTIVE)
        item2 = self._sample_item("id-2", status=QueueItemStatus.PENDING)
        item3 = self._sample_item("id-3", status=QueueItemStatus.PENDING)
        q = [item1, item2, item3]

        # Eliminar ítem pendiente
        q_after = remove_from_queue(q, "id-2")
        assert len(q_after) == 2
        ids = [i.item_id for i in q_after]
        assert "id-2" not in ids
        assert len(q) == 3  # Inmutabilidad de q

        # Intentar eliminar ítem ACTIVE (protegido)
        q_protected = remove_from_queue(q_after, "id-1")
        assert len(q_protected) == 2
        assert q_protected[0].item_id == "id-1"
        assert q_protected[0].status == QueueItemStatus.ACTIVE

        # Eliminar ID inexistente retorna copia idéntica
        q_same = remove_from_queue(q_after, "id-inexistente")
        assert len(q_same) == 2
        assert [i.item_id for i in q_same] == [i.item_id for i in q_after]

    def test_tc_1_2_3_get_next_pending_item_edge_cases(self):
        """get_next_pending_item retorna el primer PENDING o None si no hay."""
        # Cola vacía
        assert get_next_pending_item([]) is None

        # Solo ítems no pendientes
        item_act = self._sample_item("id-1", status=QueueItemStatus.ACTIVE)
        item_comp = self._sample_item("id-2", status=QueueItemStatus.COMPLETED)
        item_err = self._sample_item("id-3", status=QueueItemStatus.ERROR)
        assert get_next_pending_item([item_act, item_comp, item_err]) is None

        # Secuencia mixta
        item_pen1 = self._sample_item("id-4", status=QueueItemStatus.PENDING)
        item_pen2 = self._sample_item("id-5", status=QueueItemStatus.PENDING)
        next_item = get_next_pending_item([item_act, item_pen1, item_comp, item_pen2])
        assert next_item is not None
        assert next_item.item_id == "id-4"

    def test_tc_1_2_3_update_item_status_transitions(self):
        """update_item_status genera una nueva lista con estados y mensajes de error actualizados."""
        item1 = self._sample_item("id-1", status=QueueItemStatus.PENDING)
        item2 = self._sample_item("id-2", status=QueueItemStatus.PENDING)
        q = [item1, item2]

        # PENDING -> ACTIVE
        q_active = update_item_status(q, "id-1", QueueItemStatus.ACTIVE)
        assert q_active[0].status == QueueItemStatus.ACTIVE
        assert q[0].status == QueueItemStatus.PENDING  # Lista original intacta

        # ACTIVE -> ERROR con mensaje
        q_error = update_item_status(
            q_active,
            "id-1",
            QueueItemStatus.ERROR,
            error_msg="Error de red 403",
        )
        assert q_error[0].status == QueueItemStatus.ERROR
        assert q_error[0].error_message == "Error de red 403"

        # ACTIVE -> COMPLETED
        q_completed = update_item_status(q_active, "id-1", QueueItemStatus.COMPLETED)
        assert q_completed[0].status == QueueItemStatus.COMPLETED
        assert q_completed[0].error_message is None

        # PENDING -> CANCELLED
        q_cancelled = update_item_status(q, "id-2", QueueItemStatus.CANCELLED)
        assert q_cancelled[1].status == QueueItemStatus.CANCELLED
