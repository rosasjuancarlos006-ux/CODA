import logging
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
from utils.validator import clean_mixed_url, is_valid_youtube_url

logger = logging.getLogger(__name__)


def _default_clipboard_getter() -> str:
    """Intenta leer el portapapeles del sistema operativo de manera síncrona y segura."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        content = root.clipboard_get()
        root.destroy()
        return str(content) if content else ""
    except Exception:
        return ""


def build_home_view(
    on_mode_change: Optional[Callable[[str], None]] = None,
    on_analyze: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[str, str], None]] = None,
    clipboard_getter: Optional[Callable[[], str]] = None,
    downloads_dir: Optional[Path] = None,
) -> ft.Container:
    """
    Construye la vista de Inicio (HomeView) para Coda con validación,
    poda de enlaces y tabla de descargas recientes.
    """
    get_clipboard = clipboard_getter or _default_clipboard_getter
    target_dir = downloads_dir or config.DOWNLOADS_DIR

    # 1. Cabecera
    header_col = ft.Column(
        controls=[
            ft.Text(
                "Descarga tu música",
                size=TITLE_SIZE,
                weight=ft.FontWeight.BOLD,
                color=TEXT_PRIMARY,
            ),
            ft.Text(
                "Pega el enlace o busca canciones y playlists de YouTube y YouTube Music para guardarlas en tu equipo.",
                size=SUBTITLE_SIZE,
                color=TEXT_MUTED,
            ),
        ],
        spacing=6,
    )

    # 2. Conmutador de modo (Pestañas estilo pills de Figma)
    tab_pegar = ft.Container(
        data="paste_mode",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.LINK_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Pegar enlace", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, ACCENT_COLOR),
        border=ft.Border.all(1, ACCENT_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda _: on_mode_change("paste") if on_mode_change else None,
    )

    tab_buscar = ft.Container(
        data="search_mode",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SEARCH_ROUNDED, size=16, color=TEXT_MUTED),
                ft.Text("Buscar por nombre", size=13, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda _: on_mode_change("search") if on_mode_change else None,
    )

    mode_switcher = ft.Row(
        controls=[tab_pegar, tab_buscar],
        spacing=10,
    )

    # 3. Campo de entrada para enlace con botón de pegar y acción de análisis
    url_input = ft.TextField(
        hint_text="https://www.youtube.com/watch?v=... o https://music.youtube.com/...",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        bgcolor=SURFACE_COLOR,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        expand=True,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    def handle_paste(_):
        pasted = get_clipboard()
        if pasted:
            url_input.value = pasted.strip()
            try:
                url_input.update()
            except Exception:
                pass

    paste_button = ft.Container(
        data="paste_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CONTENT_PASTE_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Pegar", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        ink=True,
        on_click=handle_paste,
    )

    def handle_analyze(_):
        raw_url = (url_input.value or "").strip()
        if not raw_url:
            if on_error:
                on_error("Enlace vacío", "Por favor ingresa o pega un enlace de YouTube o YouTube Music.")
            return

        if not is_valid_youtube_url(raw_url):
            if on_error:
                on_error("Enlace no válido", "El enlace no parece corresponder a YouTube o YouTube Music válido.")
            return

        # Poda automática de mix de radio (&list=RD...)
        clean_url, was_pruned = clean_mixed_url(raw_url)
        if was_pruned:
            url_input.value = clean_url
            try:
                url_input.update()
            except Exception:
                pass

        if on_analyze:
            on_analyze(clean_url)

    analyze_button = ft.Container(
        data="analyze_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Analizar enlace", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
        ink=True,
        on_click=handle_analyze,
    )

    input_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[url_input, paste_button, analyze_button],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 4. Formatos soportados
    format_badges = ft.Row(
        controls=[
            ft.Text("Formatos soportados:", size=META_SIZE, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
            ft.Container(
                content=ft.Text("MP3 (320 kbps)", size=META_SIZE, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.1, TEXT_PRIMARY),
                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            ft.Container(
                content=ft.Text("M4A (AAC)", size=META_SIZE, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.1, TEXT_PRIMARY),
                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            ft.Container(
                content=ft.Text("OPUS (Original)", size=META_SIZE, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.1, TEXT_PRIMARY),
                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 5. Sección de Descargas Recientes
    recents = scan_downloaded_audio_metadata(target_dir)[:5]
    if recents:
        table_rows = []
        for r in recents:
            table_rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=16, color=ACCENT_COLOR),
                            ft.Text(r["name"], size=13, color=TEXT_PRIMARY, expand=True),
                            ft.Text(r["format"], size=12, color=TEXT_MUTED),
                            ft.Text(r["size_str"], size=12, color=TEXT_MUTED),
                            ft.Text(r["date_str"], size=11, color=TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border=ft.Border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                )
            )
        recents_content = ft.Column(controls=table_rows, spacing=4)
    else:
        recents_content = ft.Container(
            content=ft.Text("No hay descargas recientes registradas.", size=12, color=TEXT_MUTED),
            padding=ft.Padding.all(12),
        )

    recents_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.HISTORY_ROUNDED, size=18, color=TEXT_PRIMARY),
                        ft.Text("Descargas recientes", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    spacing=8,
                ),
                recents_content,
            ],
            spacing=10,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 6. Barra inferior con aviso y destino
    footer_bar = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=15, color=TEXT_MUTED),
                        ft.Text(
                            f"Destino: {target_dir.name}/",
                            size=META_SIZE,
                            color=TEXT_MUTED,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Text(
                    "Las descargas se guardan en tu equipo. Uso personal y responsable.",
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
                header_col,
                mode_switcher,
                input_card,
                format_badges,
                recents_section,
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
