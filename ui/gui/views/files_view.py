import logging
import os
import platform
from pathlib import Path
from typing import Callable, Optional
import flet as ft

import config
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
from utils.file_manager import scan_downloaded_audio_metadata

logger = logging.getLogger(__name__)


def _default_open_folder(folder_path: Path) -> None:
    """Abre la carpeta de descargas en el explorador nativo del sistema operativo."""
    folder_path.mkdir(parents=True, exist_ok=True)
    try:
        if platform.system() == "Windows":
            os.startfile(str(folder_path))
        elif platform.system() == "Darwin":
            os.system(f'open "{folder_path}"')
        else:
            os.system(f'xdg-open "{folder_path}"')
    except Exception as e:
        logger.error(f"Error abriendo explorador en {folder_path}: {e}")


def build_files_view(
    downloads_dir: Optional[Path] = None,
    on_open_folder: Optional[Callable[[], None]] = None,
    on_new_download: Optional[Callable[[], None]] = None,
) -> ft.Container:
    """
    Construye la pantalla de Archivos Descargados (FilesView) para Coda.

    Incluye:
    - Cabecera con resumen (contador de descargas y carpeta destino).
    - Botones de acción: «Abrir carpeta» y «Nueva descarga».
    - Tabla estructurada con columnas: Archivo, Tipo, Duración/Tamaño, Estado.
    - Invocación automática de `scan_downloaded_audio_metadata` para reflejar el estado actual del disco.
    - Estado vacío pedagógico si no existen archivos de audio.
    - Intangibilidad absoluta de los archivos (panel estrictamente de consulta, sin edición/borrado).
    """
    target_dir = downloads_dir or config.DOWNLOADS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # Invocación automática de escaneo de metadatos
    files = scan_downloaded_audio_metadata(target_dir)
    total_count = len(files)

    # 1. Cabecera y Resumen
    header_left = ft.Column(
        controls=[
            ft.Text(
                "Archivos descargados",
                size=TITLE_SIZE,
                weight=ft.FontWeight.BOLD,
                color=TEXT_PRIMARY,
            ),
            ft.Text(
                f"{total_count} descarga{'s' if total_count != 1 else ''} en {target_dir.name}/",
                size=SUBTITLE_SIZE,
                color=TEXT_MUTED,
            ),
        ],
        spacing=4,
    )

    open_folder_action = on_open_folder or (lambda: _default_open_folder(target_dir))

    open_folder_btn = ft.Container(
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
        padding=ft.Padding.symmetric(horizontal=16, vertical=9),
        ink=True,
        on_click=lambda _: open_folder_action(),
    )

    new_download_btn = ft.Container(
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
        padding=ft.Padding.symmetric(horizontal=18, vertical=9),
        ink=True,
        on_click=lambda _: on_new_download() if on_new_download else None,
    )

    header_bar = ft.Row(
        controls=[
            header_left,
            ft.Row(controls=[open_folder_btn, new_download_btn], spacing=10),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 2. Contenido de Archivos (Tabla o Estado Vacío)
    if total_count > 0:
        table_rows = []
        for f in files:
            file_name = f.get("name", "Audio")
            file_format = f.get("format", "MP3").upper()
            size_str = f.get("size_str", "-- MB")
            date_str = f.get("date_str", "")

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=16, color=ACCENT_COLOR),
                                    ft.Text(file_name, size=13, color=TEXT_PRIMARY, max_lines=1),
                                ],
                                spacing=8,
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(file_format, size=10, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                bgcolor=ft.Colors.with_opacity(0.12, ACCENT_COLOR),
                                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            )
                        ),
                        ft.DataCell(ft.Text(size_str, size=12, color=TEXT_MUTED)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("Guardado", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN_400),
                                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Archivo", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)),
                ft.DataColumn(ft.Text("Tipo", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)),
                ft.DataColumn(ft.Text("Tamaño", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)),
                ft.DataColumn(ft.Text("Estado", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)),
            ],
            rows=table_rows,
            heading_row_color=ft.Colors.TRANSPARENT,
            border=ft.Border.all(0, ft.Colors.TRANSPARENT),
            horizontal_margin=12,
            column_spacing=24,
            divider_thickness=1,
        )

        content_card = ft.Container(
            content=ft.Column(
                controls=[data_table],
                scroll=ft.ScrollMode.AUTO,
            ),
            bgcolor=SURFACE_COLOR,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
            padding=12,
            expand=True,
        )
    else:
        content_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=44, color=TEXT_MUTED),
                    ft.Text("No hay archivos descargados", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(
                        "Tus descargas finalizadas aparecerán catalogadas aquí de forma automática.",
                        size=12,
                        color=TEXT_MUTED,
                    ),
                    ft.Container(height=8),
                    new_download_btn,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=SURFACE_COLOR,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
            padding=48,
            alignment=ft.Alignment.CENTER,
        )

    # 3. Barra inferior informativa
    footer_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SECURITY_ROUNDED, size=15, color=TEXT_MUTED),
                        ft.Text(
                            "Tus archivos son sagrados: Coda únicamente consulta el almacenamiento sin alterar tus canciones.",
                            size=META_SIZE,
                            color=TEXT_MUTED,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Text(
                    f"Ruta: {target_dir.name}/",
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

    return ft.Container(
        content=ft.Column(
            controls=[
                header_bar,
                content_card,
                ft.Container(expand=True),
                footer_bar,
            ],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.Padding.all(24),
        expand=True,
    )
