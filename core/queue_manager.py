from dataclasses import dataclass, replace
from enum import Enum
from typing import List, Optional


class QueueItemStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    title: str
    url_or_query: str
    platform: str
    audio_format: str
    quality: str
    playlist_limit: int
    duration_str: str
    thumbnail_url: Optional[str] = None
    status: QueueItemStatus = QueueItemStatus.PENDING
    error_message: Optional[str] = None


def add_to_queue(queue: List[QueueItem], new_item: QueueItem) -> List[QueueItem]:
    """
    Agrega un nuevo QueueItem al final de la cola (orden FIFO),
    validando que no exista previamente un elemento con el mismo item_id.
    Retorna una nueva lista sin mutar la original.
    """
    for item in queue:
        if item.item_id == new_item.item_id:
            raise ValueError(f"QueueItem with id '{new_item.item_id}' already exists in queue.")
    return [*queue, new_item]


def remove_from_queue(queue: List[QueueItem], item_id: str) -> List[QueueItem]:
    """
    Extrae un elemento de la cola por su identificador único.
    Solo elimina elementos con estado PENDING; si el elemento se encuentra ACTIVE,
    no lo remueve (la cancelación activa debe seguir el protocolo de interrupción).
    Retorna una nueva lista sin mutar la original.
    """
    result: List[QueueItem] = []
    for item in queue:
        if item.item_id == item_id and item.status == QueueItemStatus.PENDING:
            continue
        result.append(item)
    return result


def get_next_pending_item(queue: List[QueueItem]) -> Optional[QueueItem]:
    """
    Retorna el primer QueueItem con estado PENDING según la secuencia FIFO,
    o None si la cola está vacía o no hay elementos pendientes.
    """
    for item in queue:
        if item.status == QueueItemStatus.PENDING:
            return item
    return None


def update_item_status(
    queue: List[QueueItem],
    item_id: str,
    new_status: QueueItemStatus,
    error_msg: Optional[str] = None,
) -> List[QueueItem]:
    """
    Produce una nueva lista de tareas con el estado actualizado del elemento especificado.
    Si se suministra error_msg, se asigna al campo error_message.
    """
    result: List[QueueItem] = []
    for item in queue:
        if item.item_id == item_id:
            result.append(replace(item, status=new_status, error_message=error_msg))
        else:
            result.append(item)
    return result
