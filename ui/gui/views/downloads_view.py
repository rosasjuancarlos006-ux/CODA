import logging
import os
import platform
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
    RADIUS_BADGE,
    TITLE_SIZE,
    SUBTITLE_SIZE,
    META_SIZE,
)

logger = logging.getLogger(__name__)

PHASE_LABELS = {
    DownloadPhase.PREPARING: "Preparación",
    DownloadPhase.DOWNLOADING: "Transferencia",
    DownloadPhase.CONVERTING: "Conversión",
    DownloadPhase.METADATA: "Metadatos",
    DownloadPhase.COMPLETED: "Completado",
    DownloadPhase.ERROR: "Error",
}


def _format_speed(bytes_per_sec: Optional[float]) -> str:
    """Formatea la velocidad de descarga a una representación legible."""
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "-- KB/s"
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    return f"{bytes_per_sec / 1024:.1f} KB/s"


def _format_eta(seconds: Optional[int]) -> str:
    """Formatea el tiempo restante estimado."""
    if seconds is None or seconds < 0:
        return "-- seg"
    if seconds >= 60:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    return f"{seconds}s"


def _open_downloads_folder(folder_path: Optional[Path] = None) -> None:
    """Abre la carpeta de descargas en el explorador del sistema operativo de manera segura."""
    target = folder_path or config.DOWNLOADS_DIR
    target.mkdir(parents=True, exist_ok=True)
    try:
        if platform.system() == "Windows":
            os.startfile(str(target))
        elif platform.system() == "Darwin":
            os.system(f'open "{target}"')
        else:
            os.system(f'xdg-open "{target}"')
    except Exception as e:
        logger.error(f"Error abriendo explorador de archivos en {target}: {e}")


def _build_step_indicator(has_active: bool, is_completed: bool = False) -> ft.Container:
    """Construye el indicador visual de pasos: Conexión lista → Descargando → Guardar archivo."""
    step1_color = ACCENT_COLOR
    step2_color = ACCENT_COLOR if (has_active or is_completed) else TEXT_MUTED
    step3_color = ACCENT_COLOR if is_completed else TEXT_MUTED

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=15, color=step1_color),
                        ft.Text("Conexión lista", size=11, color=TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    ],
                    spacing=4,
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=11, color=TEXT_MUTED),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_ROUNDED if is_completed else (
                                ft.Icons.DOWNLOAD_ROUNDED if has_active else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED
                            ),
                            size=15,
                            color=step2_color,
                        ),
                        ft.Text(
                            "Descargando",
                            size=11,
                            color=TEXT_PRIMARY if (has_active or is_completed) else TEXT_MUTED,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=11, color=TEXT_MUTED),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE_ROUNDED if is_completed else ft.Icons.SAVE_ALT_ROUNDED,
                            size=15,
                            color=step3_color,
                        ),
                        ft.Text(
                            "Guardar archivo",
                            size=11,
                            color=TEXT_PRIMARY if is_completed else TEXT_MUTED,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
    )


def _build_active_card(
    item: QueueItem,
    event: Optional[ProgressEvent],
    on_cancel: Optional[Callable[[str], None]] = None,
) -> ft.Container:
    """Construye la tarjeta de monitoreo de la tarea activa con soporte de degradación."""
    title = item.title or (event.item_title if event else "Descarga activa")
    format_name = (item.audio_format or "mp3").upper()
    platform_name = "YouTube Music" if item.platform == "youtube_music" else "YouTube"

    phase = event.phase if event else DownloadPhase.PREPARING
    phase_label = PHASE_LABELS.get(phase, "Procesando")

    pct = event.percentage if event else None
    speed_str = _format_speed(event.speed_bytes_sec if event else None)
    eta_str = _format_eta(event.eta_seconds if event else None)

    # 1. Cabecera de la tarjeta: Título, insignias y botón Cancelar
    header_row = ft.Row(
        controls=[
            ft.Container(
                content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=ACCENT_COLOR, size=24),
                bgcolor=ft.Colors.with_opacity(0.12, ACCENT_COLOR),
                border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
                width=46,
                height=46,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                controls=[
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, max_lines=1),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(phase_label, size=10, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                bgcolor=ACCENT_COLOR,
                                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                            ft.Text(f"{format_name} · {platform_name}", size=11, color=TEXT_MUTED),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=4,
                expand=True,
            ),
            ft.Container(
                key=f"cancel_active_btn_{item.item_id}",
                data="cancel_active_btn",
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.STOP_ROUNDED, size=14, color=TEXT_MUTED),
                        ft.Text("Cancelar", size=11, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.TRANSPARENT,
                border=ft.Border.all(1, BORDER_COLOR),
                border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                on_click=lambda _: on_cancel(item.item_id) if on_cancel else None,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 2. Barra de progreso
    pb_val = (pct / 100.0) if pct is not None else None
    progress_bar = ft.ProgressBar(
        value=pb_val,
        color=ACCENT_COLOR,
        bgcolor=ft.Colors.with_opacity(0.1, TEXT_PRIMARY),
        border_radius=ft.BorderRadius.all(RADIUS_BADGE),
        height=8,
    )

    pct_display = f"{pct:.1f}%" if pct is not None else phase_label
    pct_text = ft.Text(pct_display, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    # 3. Métricas en grilla horizontal
    metrics_row = ft.Row(
        controls=[
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SPEED_ROUNDED, size=14, color=TEXT_MUTED),
                    ft.Text(f"Velocidad: {speed_str}", size=11, color=TEXT_MUTED),
                ],
                spacing=4,
            ),
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TIMER_OUTLINED, size=14, color=TEXT_MUTED),
                    ft.Text(f"Restante: {eta_str}", size=11, color=TEXT_MUTED),
                ],
                spacing=4,
            ),
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=14, color=TEXT_MUTED),
                    ft.Text(f"Guardando en {config.DOWNLOADS_DIR.name}/", size=11, color=TEXT_MUTED),
                ],
                spacing=4,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    progress_sub_controls = [
        ft.Row(
            controls=[
                ft.Text("Progreso de transferencia", size=12, color=TEXT_MUTED),
                pct_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        progress_bar,
    ]

    if pct is None:
        progress_sub_controls.append(
            ft.Row(
                controls=[
                    ft.ProgressRing(color=ACCENT_COLOR, width=14, height=14, stroke_width=2),
                    ft.Text(f"Procesando ({phase_label})...", size=11, color=TEXT_MUTED),
                ],
                spacing=8,
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                header_row,
                ft.Container(height=6),
                *progress_sub_controls,
                ft.Container(height=4),
                metrics_row,
            ],
            spacing=8,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=18,
    )


def _build_queue_section(
    queue: List[QueueItem],
    on_remove: Optional[Callable[[str], None]] = None,
) -> ft.Container:
    """Construye la sección visual de la cola FIFO de espera con opción de descarte."""
    pending_items = [item for item in queue if item.status == QueueItemStatus.PENDING]
    count = len(pending_items)

    queue_cards = []
    for idx, item in enumerate(pending_items, start=1):
        queue_cards.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(str(idx), size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            width=22,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=16, color=ACCENT_COLOR),
                        ft.Text(item.title, size=13, color=TEXT_PRIMARY, expand=True, max_lines=1),
                        ft.Container(
                            content=ft.Text((item.audio_format or "mp3").upper(), size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            bgcolor=ft.Colors.with_opacity(0.08, TEXT_PRIMARY),
                            border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                        ft.Text(item.duration_str or "--:--", size=11, color=TEXT_MUTED),
                        ft.IconButton(
                            data=f"remove_queue_{item.item_id}",
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_size=16,
                            icon_color=TEXT_MUTED,
                            tooltip="Remover de la cola",
                            on_click=lambda _, iid=item.item_id: on_remove(iid) if on_remove else None,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_DARK,
                border=ft.Border.all(1, BORDER_COLOR),
                border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            )
        )

    queue_list = ft.ListView(
        controls=queue_cards,
        spacing=6,
        expand=False,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.QUEUE_MUSIC_ROUNDED, size=18, color=TEXT_PRIMARY),
                        ft.Text(
                            f"En cola de espera ({count} canción{'es' if count != 1 else ''})",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY,
                        ),
                    ],
                    spacing=8,
                ),
                queue_list,
            ],
            spacing=10,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )


def _build_success_card(
    item: Dict[str, Any],
    on_open_folder: Optional[Callable[[], None]] = None,
    on_new_download: Optional[Callable[[], None]] = None,
) -> ft.Container:
    """Construye la tarjeta de estado de 'Descarga exitosa' con resumen y acciones post-descarga."""
    title = item.get("title", "Canción descargada")
    artist = item.get("artist") or item.get("channel") or item.get("uploader") or "Artista desconocido"
    audio_format = (item.get("audio_format") or "MP3").upper()
    duration_str = item.get("duration_str", "--:--")
    size_str = item.get("size_str", "-- MB")

    open_folder_action = on_open_folder or _open_downloads_folder

    btn_open_folder = ft.Container(
        key="downloads_open_folder_btn",
        data="open_folder_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Abrir carpeta", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        ink=True,
        on_click=lambda _: open_folder_action(),
    )

    btn_new_download = ft.Container(
        key="downloads_new_download_btn",
        data="new_download_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Nueva descarga", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
        ink=True,
        on_click=lambda _: on_new_download() if on_new_download else None,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.GREEN_400, size=28),
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN_400),
                            border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
                            width=48,
                            height=48,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text("Descarga exitosa", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                        ft.Container(
                                            content=ft.Text("Guardado", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN_400),
                                            border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(f"{title} • {artist}", size=13, color=TEXT_MUTED, max_lines=1),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=BORDER_COLOR, height=20),
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.AUDIO_FILE_ROUNDED, size=14, color=TEXT_MUTED),
                                ft.Text(f"Formato: {audio_format}", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.TIMER_OUTLINED, size=14, color=TEXT_MUTED),
                                ft.Text(f"Duración: {duration_str}", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.DATA_USAGE_ROUNDED, size=14, color=TEXT_MUTED),
                                ft.Text(f"Tamaño: {size_str}", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=16,
                ),
                ft.Container(height=6),
                ft.Row(
                    controls=[btn_open_folder, btn_new_download],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=10,
                ),
            ],
            spacing=10,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, ft.Colors.GREEN_700),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=18,
    )


def build_downloads_view(
    active_item: Optional[QueueItem] = None,
    progress_event: Optional[ProgressEvent] = None,
    queue: Optional[List[QueueItem]] = None,
    completed_item: Optional[Dict[str, Any]] = None,
    on_cancel_active: Optional[Callable[[str], None]] = None,
    on_remove_from_queue: Optional[Callable[[str], None]] = None,
    on_open_folder: Optional[Callable[[], None]] = None,
    on_new_download: Optional[Callable[[], None]] = None,
) -> ft.Container:
    """
    Construye la vista de Descargas (DownloadsView) para Coda.

    Incluye:
    - Cabecera («Descargas», «Monitorea tus descargas activas y en cola.»)
    - Indicador de pasos (Conexión lista → Descargando → Guardar archivo)
    - Tarjeta de tarea activa con barra continua/indeterminada, métricas y botón «Cancelar»
    - Sección de cola de espera FIFO con remoción rápida
    - Tarjeta de «Descarga exitosa» cuando concluye una descarga y no hay tareas pendientes
    - Estado vacío pedagógico cuando no hay descargas activas ni en cola
    - Barra inferior informativa con destino de descargas (`downloads/`)
    """
    # 1. Cabecera
    header_col = ft.Column(
        controls=[
            ft.Text(
                "Descargas",
                size=TITLE_SIZE,
                weight=ft.FontWeight.BOLD,
                color=TEXT_PRIMARY,
            ),
            ft.Text(
                "Monitorea el progreso de transferencia, velocidad y tiempo estimado en tiempo real.",
                size=SUBTITLE_SIZE,
                color=TEXT_MUTED,
            ),
        ],
        spacing=6,
    )

    pending_items = [item for item in (queue or []) if item.status == QueueItemStatus.PENDING]
    has_active = (active_item is not None)
    is_completed = (completed_item is not None and not has_active and not pending_items)

    # 2. Indicador de pasos
    step_indicator = _build_step_indicator(has_active=has_active, is_completed=is_completed)

    # 3. Contenido dinámico principal (activa, exitosa o vacía)
    if has_active:
        main_card = _build_active_card(active_item, progress_event, on_cancel=on_cancel_active)
    elif is_completed and completed_item:
        main_card = _build_success_card(
            completed_item,
            on_open_folder=on_open_folder,
            on_new_download=on_new_download,
        )
    elif pending_items:
        # No hay activa en el instante pero hay cola pendiente (esperando despacho)
        main_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.ProgressRing(color=ACCENT_COLOR, width=18, height=18),
                    ft.Text("Preparando la siguiente descarga de la cola...", size=13, color=TEXT_MUTED),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=SURFACE_COLOR,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
            padding=18,
        )
    else:
        main_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, size=40, color=TEXT_MUTED),
                    ft.Text("No hay descargas activas", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(
                        "Pega un enlace o busca canciones desde Inicio para comenzar.",
                        size=12,
                        color=TEXT_MUTED,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=SURFACE_COLOR,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
            padding=32,
            alignment=ft.Alignment.CENTER,
        )

    # 4. Sección de cola FIFO si existen elementos pendientes
    queue_section = _build_queue_section(pending_items, on_remove=on_remove_from_queue) if pending_items else None

    # 5. Barra inferior informativa
    footer_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=15, color=TEXT_MUTED),
                        ft.Text(f"Destino: {config.DOWNLOADS_DIR.name}/", size=META_SIZE, color=TEXT_MUTED),
                    ],
                    spacing=6,
                ),
                ft.Text(
                    "Descargas secuenciales FIFO: una canción se procesa a la vez.",
                    size=META_SIZE,
                    color=TEXT_MUTED,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
    )

    body_controls = [
        header_col,
        step_indicator,
        main_card,
    ]
    if queue_section:
        body_controls.append(queue_section)

    body_controls.append(ft.Container(expand=True))
    body_controls.append(footer_bar)

    return ft.Container(
        content=ft.Column(
            controls=body_controls,
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.Padding.all(24),
        expand=True,
    )
