import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import flet as ft

import config
from core.events import DownloadPhase, ProgressEvent
from core.queue_manager import QueueItem, QueueItemStatus
from ui.gui.theme import (
    BG_DARK,
    SURFACE_COLOR,
    ACCENT_COLOR,
    TEXT_PRIMARY,
    TEXT_MUTED,
    BORDER_COLOR,
    RADIUS_CONTAINER,
    RADIUS_BUTTON,
    build_coda_theme,
)
from ui.gui.views.downloads_view import build_downloads_view
from ui.gui.views.files_view import build_files_view
from ui.gui.views.home_view import build_home_view
from ui.gui.views.options_view import build_options_view
from ui.gui.views.search_view import build_search_view
from ui.gui.views.sidebar import build_sidebar
from ui.view_interface import ViewInterface
from utils.file_manager import AudioFileInfo
from utils.validator import is_playlist_url

logger = logging.getLogger(__name__)


class FletView:
    """
    Concrete implementation of ViewInterface using Flet for the graphical user interface.
    Manages the window frame, sidebar navigation, dynamic central panels, and toasts/modals.
    """

    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.current_section: str = "inicio"
        self.queue_items: List[Any] = []
        self.active_progress: Optional[ProgressEvent] = None
        self.has_active_download: bool = False
        self.controller: Any = None
        self.output_dir: Path = config.DOWNLOADS_DIR

        # Estado para vistas dinámicas
        self.search_results: List[Dict[str, Any]] = []
        self.is_searching: bool = False
        self.selected_track_for_options: Optional[Dict[str, Any]] = None
        self.last_completed_item: Optional[Dict[str, Any]] = None

        # UI Containers
        self._sidebar_container: Optional[ft.Container] = None
        self._content_container: Optional[ft.Container] = None
        self._section_cache: Dict[str, ft.Control] = {}
        self._last_progress_render_ts: float = 0.0
        self._progress_throttle_interval: float = 0.1  # 100 ms máximo de refresco pesado en progreso

    def set_controller(self, controller: Any) -> None:
        """Asocia el GUIController a la vista."""
        self.controller = controller
        if hasattr(controller, "output_dir"):
            self.output_dir = Path(controller.output_dir)

    def init_page(self, page: ft.Page) -> None:
        """Configura la ventana principal y ensambla el layout raíz con Flet."""
        self.page = page
        self.page.title = "CODA · Tu música, en tus archivos."
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = build_coda_theme()
        self.page.bgcolor = BG_DARK
        self.page.padding = ft.Padding.all(0)

        # Configuración de ventana nativa de escritorio
        try:
            if not hasattr(self.page, "window") or self.page.window is None:
                self.page.window = ft.Window()
            self.page.window.width = 1024
            self.page.window.height = 700
            self.page.window.min_width = 800
            self.page.window.min_height = 600
            self.page.window.resizable = True
            self.page.window.maximizable = True
            self.page.window.minimizable = True
            self.page.window.shadow = True
            self.page.window.prevent_close = True
            self.page.window.on_event = self._handle_window_event
        except Exception as e:
            logger.debug(f"Aviso configurando page.window: {e}")

        # Barra lateral y panel central
        self._rebuild_sidebar()
        self._content_container = ft.Container(
            expand=True,
            bgcolor=BG_DARK,
            content=self._get_section_content(self.current_section),
        )

        root_layout = ft.Row(
            controls=[
                self._sidebar_container,
                self._content_container,
            ],
            spacing=0,
            expand=True,
        )

        self.page.add(root_layout)
        self.page.update()

    def _handle_window_event(self, e: Any) -> None:
        """Maneja eventos nativos de la ventana del sistema operativo."""
        event_type = getattr(e, "type", getattr(e, "data", str(e)))
        if "close" in str(event_type).lower():
            if self.has_active_download:
                self.confirm_window_close(on_confirm=self._force_close_window)
            else:
                self._force_close_window()

    def _force_close_window(self) -> None:
        """Cierra definitivamente la aplicación."""
        if self.page and hasattr(self.page, "window") and self.page.window:
            self.page.window.prevent_close = False
            try:
                self.page.window.destroy()
            except Exception:
                pass

    def confirm_window_close(self, on_confirm: Optional[Callable[[], None]] = None) -> None:
        """Muestra diálogo de confirmación pedagógico al cerrar la ventana con descargas activas."""
        if not self.page:
            return

        def handle_cancel(_):
            if hasattr(self.page, "pop_dialog"):
                self.page.pop_dialog()
            dialog.open = False
            self._safe_update(dialog)

        def handle_exit(_):
            if hasattr(self.page, "pop_dialog"):
                self.page.pop_dialog()
            dialog.open = False
            self._safe_update(dialog)
            if on_confirm:
                on_confirm()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Descargas en curso", weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
            content=ft.Text(
                "Hay descargas activas en ejecución. Si cierras la aplicación ahora, "
                "se cancelarán las operaciones actuales y se limpiarán los archivos temporales.\n\n"
                "¿Deseas salir de todas formas?",
                color=TEXT_PRIMARY,
                size=13,
            ),
            bgcolor=SURFACE_COLOR,
            actions=[
                ft.TextButton(
                    key="close_dialog_cancel_btn",
                    content=ft.Text("Continuar descargando", color=TEXT_PRIMARY),
                    on_click=handle_cancel,
                ),
                ft.FilledButton(
                    key="close_dialog_confirm_btn",
                    content=ft.Text("Cerrar y salir", color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                    bgcolor=ACCENT_COLOR,
                    on_click=handle_exit,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dialog)

    def _safe_update(self, control: Optional[ft.Control] = None) -> None:
        """Actualiza el control de forma segura o la página completa sin lanzar excepción si no está montado."""
        if not self.page:
            return
        try:
            if control is not None:
                control.update()
            else:
                self.page.update()
        except RuntimeError:
            try:
                self.page.update()
            except Exception:
                pass
        except Exception:
            pass

    def _rebuild_sidebar(self) -> None:
        """Reconstruye el sidebar manteniendo el estado de sección y conteo de cola."""
        sidebar_ctrl = build_sidebar(
            current_section=self.current_section,
            queue_count=len(self.queue_items),
            on_navigate=self.navigate_to_section,
        )
        if self._sidebar_container is None:
            self._sidebar_container = sidebar_ctrl
        else:
            self._sidebar_container.content = sidebar_ctrl.content
            self._safe_update(self._sidebar_container)

    def _handle_analyze_url(self, clean_url: str) -> None:
        """Callback al analizar una URL válida desde Inicio."""
        is_pl = is_playlist_url(clean_url)
        self.selected_track_for_options = {
            "title": "Lista de reproducción" if is_pl else "Canción analizada",
            "artist": "YouTube",
            "duration_str": "--:--",
            "url": clean_url,
            "is_playlist": is_pl,
        }
        self.navigate_to_section("opciones")

    def _handle_select_track_from_search(self, track: Dict[str, Any]) -> None:
        """Callback al elegir una pista desde los resultados de búsqueda."""
        self.selected_track_for_options = dict(track)
        self.navigate_to_section("opciones")

    def _handle_start_download_from_options(self, options_data: Dict[str, Any]) -> None:
        """Encola la tarea configurada y transiciona a descargas o avisa con toast."""
        item_id = str(os.urandom(8).hex())

        # El payload proveniente de OptionsView puede ser plano o anidado bajo 'track'
        track = options_data.get("track") if isinstance(options_data.get("track"), dict) else options_data

        url_val = (
            track.get("url")
            or track.get("url_or_query")
            or options_data.get("url")
            or options_data.get("url_or_query")
            or ""
        )
        title_val = (
            track.get("title")
            or options_data.get("title")
            or "Canción seleccionada"
        )
        format_val = (
            options_data.get("audio_format")
            or options_data.get("format")
            or track.get("audio_format")
            or track.get("format")
            or "mp3"
        )
        duration_val = (
            track.get("duration_str")
            or options_data.get("duration_str")
            or "--:--"
        )

        new_item = QueueItem(
            item_id=item_id,
            title=title_val,
            url_or_query=url_val,
            platform=options_data.get("platform", "youtube"),
            audio_format=format_val,
            quality="auto",
            playlist_limit=options_data.get("playlist_limit") or 0,
            duration_str=duration_val,
            status=QueueItemStatus.PENDING,
        )

        if self.controller:
            self.controller.encolar_tarea(new_item)
        else:
            self.show_toast("Descarga encolada.")
            self.navigate_to_section("descargas")

    def _get_section_content(self, section: str) -> ft.Control:
        """Retorna el contenedor funcional de la sección correspondiente."""
        section_key = section.lower()

        if section_key == "inicio":
            return build_home_view(
                on_mode_change=lambda mode: self.navigate_to_section("busqueda" if mode == "search" else "inicio"),
                on_analyze=self._handle_analyze_url,
                on_error=lambda title, msg: self.show_modal_error(title, msg, ["Aceptar"]),
                downloads_dir=self.output_dir,
            )

        elif section_key == "busqueda":
            return build_search_view(
                initial_query="",
                results=self.search_results,
                is_loading=self.is_searching,
                on_mode_change=lambda mode: self.navigate_to_section("inicio" if mode == "paste" else "busqueda"),
                on_search=lambda term: self.controller.buscar_por_nombre(term) if self.controller else None,
                on_select_track=self._handle_select_track_from_search,
                on_error=lambda title, msg: self.show_modal_error(title, msg, ["Aceptar"]),
            )

        elif section_key == "opciones":
            return build_options_view(
                track_info=self.selected_track_for_options,
                on_cancel=lambda: self.navigate_to_section("inicio"),
                on_start_download=self._handle_start_download_from_options,
            )

        elif section_key == "descargas":
            active_item = None
            pending_items = []
            for item in self.queue_items:
                st = getattr(item, "status", None)
                st_val = getattr(st, "value", str(st)).lower()
                if st_val == "active" and active_item is None:
                    active_item = item
                elif st_val == "pending":
                    pending_items.append(item)

            return build_downloads_view(
                active_item=active_item,
                progress_event=self.active_progress,
                queue=pending_items,
                completed_item=self.last_completed_item,
                on_cancel_active=lambda item_id: self.controller.cancelar_tarea_activa(item_id) if self.controller else None,
                on_remove_from_queue=lambda item_id: self.controller.remover_de_cola(item_id) if self.controller else None,
                on_open_folder=self._open_downloads_folder,
                on_new_download=lambda: self.navigate_to_section("inicio"),
            )

        elif section_key == "archivos":
            return build_files_view(
                downloads_dir=self.output_dir,
                on_open_folder=self._open_downloads_folder,
                on_new_download=lambda: self.navigate_to_section("inicio"),
            )

        # Fallback genérico si se solicita una sección desconocida
        placeholder = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(section_key.capitalize(), size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Sección lista.", size=13, color=TEXT_MUTED),
                ],
                spacing=8,
            ),
            padding=ft.Padding.all(24),
            expand=True,
        )
        return placeholder

    def _open_downloads_folder(self) -> None:
        """Abre la carpeta de descargas en el explorador nativo."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(self.output_dir))
            elif platform.system() == "Darwin":
                os.system(f'open "{self.output_dir}"')
            else:
                os.system(f'xdg-open "{self.output_dir}"')
        except Exception as e:
            logger.warning(f"No se pudo abrir explorador en {self.output_dir}: {e}")

    # --- Métodos del Contrato ViewInterface ---

    def navigate_to_section(self, section: str) -> None:
        """Conmuta dinámicamente el panel central entre las secciones sin perder el estado."""
        self.current_section = section.lower()
        if self._content_container:
            self._content_container.content = self._get_section_content(self.current_section)
            self._safe_update(self._content_container)
        self._rebuild_sidebar()
        logger.debug(f"GUI navegó a sección: {self.current_section}")

    def show_toast(self, message: str) -> None:
        """Despliega una notificación breve y no intrusiva con SnackBar."""
        if not self.page:
            return

        snack = ft.SnackBar(
            content=ft.Text(message, color=TEXT_PRIMARY),
            bgcolor=SURFACE_COLOR,
            show_close_icon=True,
            close_icon_color=ACCENT_COLOR,
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(snack)
        elif hasattr(self.page, "overlay"):
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def show_modal_error(
        self,
        title: str,
        message: str,
        buttons: Optional[List[str]] = None,
        on_action: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Despliega un diálogo modal de error pedagógico con ícono de alerta y opciones
        de acción claras («Reintentar» / «Aceptar / Volver al inicio»).
        """
        logger.error(f"GUI Error modal [{title}]: {message}")
        btn_labels = buttons or ["Reintentar", "Aceptar / Volver al inicio"]

        if self.page:
            action_buttons = []
            for idx, label in enumerate(btn_labels):
                def make_handler(btn_txt=label):
                    def handler(_):
                        if hasattr(self.page, "pop_dialog"):
                            self.page.pop_dialog()
                        dialog.open = False
                        self._safe_update(dialog)
                        if on_action:
                            on_action(btn_txt)
                    return handler

                # Normalizar clave para testing y flet[test]
                btn_key = f"error_modal_btn_{label.lower().replace(' ', '_').replace('/', '_')}"

                # El primer botón estilo primario
                if idx == 0:
                    action_buttons.append(
                        ft.FilledButton(
                            key=btn_key,
                            content=ft.Text(label, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                            bgcolor=ACCENT_COLOR,
                            on_click=make_handler(),
                        )
                    )
                else:
                    action_buttons.append(
                        ft.TextButton(
                            key=btn_key,
                            content=ft.Text(label, color=TEXT_MUTED),
                            on_click=make_handler(),
                        )
                    )

            dialog = ft.AlertDialog(
                modal=True,
                icon=ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, color=ACCENT_COLOR, size=32),
                title=ft.Text(title, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, size=16),
                content=ft.Text(message, color=TEXT_PRIMARY, size=13),
                bgcolor=SURFACE_COLOR,
                actions=action_buttons,
                actions_alignment=ft.MainAxisAlignment.END,
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(dialog)

        return btn_labels[0] if btn_labels else "Aceptar"

    def show_search_results(self, results: List[Dict[str, Any]]) -> None:
        """Muestra los resultados de búsqueda para selección interactiva."""
        logger.info(f"GUI recibió {len(results)} resultados de búsqueda.")
        self.search_results = list(results)
        self.is_searching = False
        self.navigate_to_section("busqueda")

    def show_queue_state(self, queue: List[Any]) -> None:
        """Actualiza el estado visual de la cola de descargas."""
        self.queue_items = list(queue)
        self.has_active_download = any(
            getattr(item, "status", None) == "active" or getattr(getattr(item, "status", None), "value", None) == "active"
            for item in self.queue_items
        )
        self._rebuild_sidebar()
        if self.current_section == "descargas":
            if self._content_container:
                self._content_container.content = self._get_section_content("descargas")
                self._safe_update(self._content_container)

    def show_banner(self) -> None:
        pass

    def show_main_menu(self) -> str:
        return "1"

    def prompt_platform(self) -> str:
        return "youtube"

    def prompt_query(self, platform_name: str) -> str:
        return ""

    def prompt_playlist_limit(self) -> Optional[int]:
        return None

    def prompt_audio_format(self, is_playlist: bool) -> str:
        return "mp3"

    def show_platform_mismatch(self, selected: str, adapted: str) -> None:
        self.show_toast(f"Plataforma adaptada automáticamente a: {adapted}")

    def show_info(self, message: str) -> None:
        self.show_toast(message)

    def show_warning(self, message: str) -> None:
        self.show_toast(f"Aviso: {message}")

    def show_error(self, message: str, error_type: Optional[str] = None) -> None:
        self.show_modal_error("Error", message, ["Aceptar"])

    def show_single_success(self, result: Dict[str, Any]) -> None:
        self.last_completed_item = dict(result)
        title = result.get("title", "Canción")
        self.show_toast(f"Descargado con éxito: {title}")
        if self.current_section == "descargas" and self._content_container:
            self._content_container.content = self._get_section_content("descargas")
            self._safe_update(self._content_container)

    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None:
        total = summary.get("total", 0)
        self.show_toast(f"Playlist completada: {total} pista(s)")

    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None:
        pass

    def show_empty_downloads(self) -> None:
        pass

    def on_progress(self, event: ProgressEvent) -> None:
        self.active_progress = event
        if self.current_section == "descargas" and self._content_container:
            now = time.time()
            # Actualización inmediata en cambios de fase críticos o respetando el intervalo de throttle
            is_critical_phase = event.phase in (
                DownloadPhase.COMPLETED,
                DownloadPhase.ERROR,
                DownloadPhase.CONVERTING,
                DownloadPhase.METADATA,
                DownloadPhase.PREPARING,
            )
            if is_critical_phase or (now - self._last_progress_render_ts) >= self._progress_throttle_interval:
                self._last_progress_render_ts = now
                self._content_container.content = self._get_section_content("descargas")
                self._safe_update(self._content_container)

    def start_progress_task(self, title: str, total: Optional[int] = None) -> None:
        pass

    def stop_progress_task(self) -> None:
        pass
