import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from core.downloader import (
    download_audio_from_youtube,
    download_playlist,
)
from core.events import DownloadPhase, ProgressEvent
from core.queue_manager import (
    QueueItem,
    QueueItemStatus,
    add_to_queue,
    get_next_pending_item,
    remove_from_queue,
    update_item_status,
)
from core.resolver import buscar_top_coincidencias
from ui.view_interface import ViewInterface
from utils.file_manager import cleanup_files, find_partial_download_files
from utils.validator import is_playlist_url

logger = logging.getLogger(__name__)


class GUIController:
    """
    Controlador para la interfaz gráfica (GUI) de Coda.

    Responsable de:
    - Gestionar el estado de la cola FIFO de descargas.
    - Decidir la navegación y avisos no invasivos al encolar tareas.
    - Orquestar la adición y remoción anticipada de tareas.
    - Despachar en hilo secundario el procesamiento secuencial FIFO.
    - Manejar la cancelación activa con limpieza de temporales.
    """

    def __init__(self, view: ViewInterface, output_dir: Path, autostart_worker: bool = True):
        self.view = view
        self.output_dir = Path(output_dir)
        self.cola_descargas: List[QueueItem] = []
        self.is_running: bool = True
        self.is_searching: bool = False
        self.cancellation_requested: bool = False
        self._active_item_id: Optional[str] = None
        self._lock = threading.Lock()

        # Iniciar despachador en hilo secundario daemon
        self._worker_thread: Optional[threading.Thread] = None
        if autostart_worker:
            self._worker_thread = threading.Thread(
                target=self._queue_dispatcher_worker,
                daemon=True,
                name="CodaQueueDispatcher",
            )
            self._worker_thread.start()

    def hay_tarea_activa(self) -> bool:
        """Determina si actualmente existe una tarea en estado ACTIVE en la cola."""
        with self._lock:
            return any(item.status == QueueItemStatus.ACTIVE for item in self.cola_descargas)

    def encolar_tarea(self, item: QueueItem) -> None:
        """
        Encola una nueva tarea al final de la colección FIFO.

        Regla de navegación:
        - Si no hay descargas activas previas, redirige de inmediato a la sección 'descargas'.
        - Si ya existe una descarga en curso, no interrumpe el flujo del usuario y emite
          una notificación no invasiva (toast) 'Agregado a la cola de descargas'.
        """
        tenia_activa = self.hay_tarea_activa()

        with self._lock:
            self.cola_descargas = add_to_queue(self.cola_descargas, item)
            current_state = list(self.cola_descargas)

        self.view.show_queue_state(current_state)

        if not tenia_activa:
            logger.info(f"Primera tarea encolada: {item.title}. Redirigiendo a descargas.")
            self.view.navigate_to_section("descargas")
        else:
            logger.info(f"Tarea encolada en segundo plano: {item.title}. Notificando toast.")
            self.view.show_toast(f"«{item.title}» agregado a la cola de descargas.")

    def remover_de_cola(self, item_id: str) -> None:
        """
        Remueve un elemento pendiente de la cola antes de que inicie su ejecución.
        No afecta tareas que ya se encuentren en ejecución (ACTIVE).
        """
        with self._lock:
            self.cola_descargas = remove_from_queue(self.cola_descargas, item_id)
            current_state = list(self.cola_descargas)

        self.view.show_queue_state(current_state)
        logger.info(f"Elemento con id {item_id} removido de la cola.")

    def cancelar_tarea_activa(self, item_id: Optional[str] = None) -> None:
        """
        Solicita la cancelación de la descarga activa, purga los archivos temporales
        residuales generados y despacha la siguiente tarea o navega a Inicio.
        """
        with self._lock:
            target_id = item_id or self._active_item_id
            if not target_id:
                return

            self.cancellation_requested = True
            logger.info(f"Cancelación solicitada para la tarea activa {target_id}.")

            # Marcar CANCELLED en la cola
            self.cola_descargas = update_item_status(self.cola_descargas, target_id, QueueItemStatus.CANCELLED)
            self._active_item_id = None
            current_state = list(self.cola_descargas)

        # Limpiar archivos temporales parciales
        self._limpiar_temporales()

        self.view.show_queue_state(current_state)

        # Decisión de navegación post-cancelación
        with self._lock:
            hay_pendientes = any(i.status == QueueItemStatus.PENDING for i in self.cola_descargas)

        if hay_pendientes:
            self.view.show_toast("Descarga cancelada. Iniciando siguiente pista.")
        else:
            self.view.show_toast("Descarga cancelada.")
            self.view.navigate_to_section("inicio")

    def _limpiar_temporales(self, start_time: Optional[float] = None) -> None:
        """Purga cualquier archivo temporal (.part, .ytdl, etc.) en output_dir."""
        try:
            ts = start_time or 0.0
            partials = find_partial_download_files(self.output_dir, ts)
            if partials:
                cleaned = cleanup_files(partials)
                logger.debug(f"Limpieza de temporales: {cleaned} archivo(s) eliminados.")
        except Exception as e:
            logger.warning(f"Error purgando temporales: {e}")

    def _process_next_queue_item(self) -> bool:
        """
        Procesa sincrónicamente una única tarea de la cola FIFO.
        Retorna True si procesó un ítem, o False si la cola estaba vacía.
        """
        with self._lock:
            item = get_next_pending_item(self.cola_descargas)
            if item is None:
                return False

            # Iniciar tarea activa
            self.cancellation_requested = False
            self._active_item_id = item.item_id
            self.cola_descargas = update_item_status(self.cola_descargas, item.item_id, QueueItemStatus.ACTIVE)
            current_state = list(self.cola_descargas)

        self.view.show_queue_state(current_state)
        start_ts = time.time()

        def progress_callback(event: ProgressEvent):
            if self.cancellation_requested:
                return
            self.view.on_progress(event)

        try:
            # Ejecutar descarga con motor desacoplado
            if is_playlist_url(item.url_or_query):
                res = download_playlist(
                    playlist_url=item.url_or_query,
                    output_dir=self.output_dir,
                    limit=item.playlist_limit or 0,
                    audio_format=item.audio_format,
                    on_progress=progress_callback,
                )
            else:
                res = download_audio_from_youtube(
                    query=item.url_or_query,
                    output_dir=self.output_dir,
                    audio_format=item.audio_format,
                    on_progress=progress_callback,
                )

            # Verificar si se canceló en pleno proceso
            if self.cancellation_requested:
                self._limpiar_temporales(start_ts)
                return True

            if res.get("success", False):
                with self._lock:
                    self.cola_descargas = update_item_status(self.cola_descargas, item.item_id, QueueItemStatus.COMPLETED)
                    self._active_item_id = None
                    final_state = list(self.cola_descargas)

                self.view.show_queue_state(final_state)
                self.view.show_single_success(res)
            else:
                # Fallo operativo
                error_msg = res.get("message") or res.get("error") or "Error durante la descarga"
                self._limpiar_temporales(start_ts)

                with self._lock:
                    self.cola_descargas = update_item_status(
                        self.cola_descargas,
                        item.item_id,
                        QueueItemStatus.ERROR,
                        error_msg=error_msg,
                    )
                    self._active_item_id = None
                    final_state = list(self.cola_descargas)

                self.view.show_queue_state(final_state)
                self.view.show_modal_error(
                    title="Error en la descarga",
                    message=f"No se pudo completar «{item.title}»: {error_msg}",
                    buttons=["Aceptar"],
                )

        except Exception as e:
            logger.exception(f"Excepción inesperada en worker para {item.title}: {e}")
            self._limpiar_temporales(start_ts)
            with self._lock:
                self.cola_descargas = update_item_status(
                    self.cola_descargas,
                    item.item_id,
                    QueueItemStatus.ERROR,
                    error_msg=str(e),
                )
                self._active_item_id = None
                final_state = list(self.cola_descargas)

            self.view.show_queue_state(final_state)
            self.view.show_modal_error(
                title="Error inesperado",
                message=f"Ocurrió un error al procesar «{item.title}»: {e}",
                buttons=["Aceptar"],
            )

        return True

    def _queue_dispatcher_worker(self) -> None:
        """Bucle infinito del hilo despachador FIFO."""
        logger.info("Despachador FIFO de cola iniciado en segundo plano.")
        while self.is_running:
            try:
                processed = self._process_next_queue_item()
                if not processed:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error no controlado en hilo de cola: {e}")
                time.sleep(0.5)

    def stop(self) -> None:
        """Detiene la ejecución del worker en segundo plano."""
        self.is_running = False

    def buscar_por_nombre(self, termino: str, platform: str = "youtube", synchronous: bool = False) -> None:
        """
        Ejecuta la búsqueda de los 5 mejores resultados sin bloquear la interfaz de usuario.
        Si synchronous es True (útil para pruebas unitarias deterministas), se ejecuta en el hilo invocador.
        """
        def _task():
            cleaned = (termino or "").strip()
            if not cleaned:
                return

            self.is_searching = True
            logger.info(f"Iniciando búsqueda de coincidencias para '{cleaned}'...")

            try:
                results = buscar_top_coincidencias(cleaned, limite=5, platform=platform)
                if not results:
                    self.view.show_modal_error(
                        title="Sin coincidencias",
                        message=f"No se encontraron canciones para el término «{cleaned}». Intenta con otro nombre o artista.",
                        buttons=["Aceptar"],
                    )
                else:
                    self.view.show_search_results(results)
            except Exception as e:
                logger.error(f"Error consultando resultados para '{cleaned}': {e}")
                self.view.show_modal_error(
                    title="Error de conexión",
                    message="No fue posible conectar con el servicio de búsqueda. Verifica tu conexión a internet e inténtalo nuevamente.",
                    buttons=["Reintentar", "Aceptar"],
                )
            finally:
                self.is_searching = False

        if synchronous:
            _task()
        else:
            search_thread = threading.Thread(
                target=_task,
                daemon=True,
                name=f"CodaSearch-{termino[:10]}",
            )
            search_thread.start()

