import pytest
from dataclasses import FrozenInstanceError

def test_queue_item_status_enum_values():
    """
    Verifica que el enum QueueItemStatus contenga los estados requeridos.
    """
    from core.queue_manager import QueueItemStatus

    assert QueueItemStatus.PENDING.value == "pending"
    assert QueueItemStatus.ACTIVE.value == "active"
    assert QueueItemStatus.COMPLETED.value == "completed"
    assert QueueItemStatus.CANCELLED.value == "cancelled"
    assert QueueItemStatus.ERROR.value == "error"


def test_queue_item_instantiation_and_defaults():
    """
    Verifica la instanciación de QueueItem con sus campos requeridos y valores predeterminados.
    """
    from core.queue_manager import QueueItem, QueueItemStatus

    item = QueueItem(
        item_id="task-123",
        title="Noches de neón",
        url_or_query="https://www.youtube.com/watch?v=example",
        platform="youtube",
        audio_format="mp3",
        quality="auto",
        playlist_limit=0,
        duration_str="3:42",
    )

    assert item.item_id == "task-123"
    assert item.title == "Noches de neón"
    assert item.url_or_query == "https://www.youtube.com/watch?v=example"
    assert item.platform == "youtube"
    assert item.audio_format == "mp3"
    assert item.quality == "auto"
    assert item.playlist_limit == 0
    assert item.duration_str == "3:42"
    assert item.thumbnail_url is None
    assert item.status == QueueItemStatus.PENDING
    assert item.error_message is None


def test_queue_item_is_immutable():
    """
    Verifica que QueueItem sea inmutable (frozen=True) para garantizar
    la seguridad de estado en el modelo puro de dominio.
    """
    from core.queue_manager import QueueItem, QueueItemStatus

    item = QueueItem(
        item_id="task-123",
        title="Canción inmutable",
        url_or_query="query",
        platform="youtube",
        audio_format="mp3",
        quality="auto",
        playlist_limit=0,
        duration_str="2:30",
    )

    with pytest.raises(FrozenInstanceError):
        item.status = QueueItemStatus.ACTIVE  # type: ignore


def test_queue_manager_does_not_import_ui():
    """
    Verifica que core/queue_manager.py no importe nada de la capa de interfaz (ui/).
    Regla 3 de la Constitución.
    """
    import core.queue_manager as qm

    imported_modules = dir(qm)
    assert "ui" not in imported_modules
    assert "flet" not in imported_modules
    assert "rich" not in imported_modules


def _create_sample_item(item_id: str, title: str = "Test", status=None):
    from core.queue_manager import QueueItem, QueueItemStatus
    return QueueItem(
        item_id=item_id,
        title=title,
        url_or_query="url",
        platform="youtube",
        audio_format="mp3",
        quality="auto",
        playlist_limit=0,
        duration_str="3:00",
        status=status or QueueItemStatus.PENDING
    )


def test_add_to_queue_appends_and_validates_unique_id():
    """
    1. Verifica que add_to_queue agregue elementos al final respetando orden FIFO
    y no permita IDs duplicados.
    """
    from core.queue_manager import add_to_queue

    item1 = _create_sample_item("1", "Song 1")
    item2 = _create_sample_item("2", "Song 2")

    q0 = []
    q1 = add_to_queue(q0, item1)
    assert len(q1) == 1
    assert q1[0] == item1

    q2 = add_to_queue(q1, item2)
    assert len(q2) == 2
    assert q2[0] == item1
    assert q2[1] == item2

    # Intentar agregar un item con id repetido debe lanzar ValueError
    dup_item = _create_sample_item("1", "Duplicate")
    with pytest.raises(ValueError, match="already exists"):
        add_to_queue(q2, dup_item)


def test_remove_from_queue_removes_pending_only():
    """
    2. Verifica que remove_from_queue elimine tareas con estado PENDING por ID.
    """
    from core.queue_manager import remove_from_queue, QueueItemStatus

    item1 = _create_sample_item("1", "Song 1", status=QueueItemStatus.PENDING)
    item2 = _create_sample_item("2", "Song 2", status=QueueItemStatus.PENDING)

    q = [item1, item2]
    q_after = remove_from_queue(q, "1")
    assert len(q_after) == 1
    assert q_after[0].item_id == "2"


def test_remove_from_queue_protects_active_item():
    """
    3. Verifica la protección de elemento activo: una tarea ACTIVE no se elimina
    mediante remove_from_queue (requiere flujo de cancelación explícito).
    """
    from core.queue_manager import remove_from_queue, QueueItemStatus

    item_active = _create_sample_item("act", "Active Song", status=QueueItemStatus.ACTIVE)
    item_pending = _create_sample_item("pen", "Pending Song", status=QueueItemStatus.PENDING)

    q = [item_active, item_pending]
    q_after = remove_from_queue(q, "act")
    assert len(q_after) == 2
    assert q_after[0] == item_active
    assert q_after[1] == item_pending


def test_remove_from_queue_nonexistent_id_returns_same_list():
    """
    4. Verifica que remover un ID inexistente devuelva la lista sin cambios.
    """
    from core.queue_manager import remove_from_queue

    item1 = _create_sample_item("1", "Song 1")
    q = [item1]
    q_after = remove_from_queue(q, "999")
    assert q_after == q


def test_get_next_pending_item_empty_returns_none():
    """
    5. Verifica que get_next_pending_item retorne None con cola vacía o sin tareas pendientes.
    """
    from core.queue_manager import get_next_pending_item, QueueItemStatus

    assert get_next_pending_item([]) is None

    item_active = _create_sample_item("1", status=QueueItemStatus.ACTIVE)
    item_completed = _create_sample_item("2", status=QueueItemStatus.COMPLETED)
    assert get_next_pending_item([item_active, item_completed]) is None


def test_get_next_pending_item_fifo_selection():
    """
    6. Verifica que get_next_pending_item seleccione el primer elemento PENDING en orden FIFO.
    """
    from core.queue_manager import get_next_pending_item, QueueItemStatus

    item_active = _create_sample_item("1", status=QueueItemStatus.ACTIVE)
    item_pending1 = _create_sample_item("2", status=QueueItemStatus.PENDING)
    item_pending2 = _create_sample_item("3", status=QueueItemStatus.PENDING)

    q = [item_active, item_pending1, item_pending2]
    next_item = get_next_pending_item(q)
    assert next_item == item_pending1


def test_update_item_status_transitions_and_errors():
    """
    7. Verifica transiciones válidas de estado (PENDING -> ACTIVE -> COMPLETED / CANCELLED / ERROR)
    y asignación de mensaje de error.
    """
    from core.queue_manager import update_item_status, QueueItemStatus

    item1 = _create_sample_item("1", status=QueueItemStatus.PENDING)
    q = [item1]

    # PENDING -> ACTIVE
    q_active = update_item_status(q, "1", QueueItemStatus.ACTIVE)
    assert q_active[0].status == QueueItemStatus.ACTIVE

    # ACTIVE -> COMPLETED
    q_completed = update_item_status(q_active, "1", QueueItemStatus.COMPLETED)
    assert q_completed[0].status == QueueItemStatus.COMPLETED

    # ACTIVE -> CANCELLED
    q_cancelled = update_item_status(q_active, "1", QueueItemStatus.CANCELLED)
    assert q_cancelled[0].status == QueueItemStatus.CANCELLED

    # ACTIVE -> ERROR con mensaje
    q_error = update_item_status(q_active, "1", QueueItemStatus.ERROR, error_msg="Error de red")
    assert q_error[0].status == QueueItemStatus.ERROR
    assert q_error[0].error_message == "Error de red"

    # Actualizar id inexistente
    q_unchanged = update_item_status(q_error, "nonexistent", QueueItemStatus.COMPLETED)
    assert q_unchanged == q_error
