import logging
from typing import Any, Callable, Dict, List, Optional
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

logger = logging.getLogger(__name__)


def _build_result_card(
    item: Dict[str, Any],
    on_select: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> ft.Container:
    """Construye una tarjeta individual para un resultado de búsqueda."""
    title = item.get("title", "Canción desconocida")
    artist = item.get("artist") or item.get("channel") or item.get("uploader") or "Artista desconocido"
    version = item.get("version", "Audio oficial")
    duration = item.get("duration_str", "--:--")
    item_id = item.get("id", "0")

    # Icono o carátula fallback
    icon_container = ft.Container(
        content=ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, color=ACCENT_COLOR, size=24),
        bgcolor=ft.Colors.with_opacity(0.12, ACCENT_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        width=48,
        height=48,
        alignment=ft.Alignment.CENTER,
    )

    info_col = ft.Column(
        controls=[
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, max_lines=1),
            ft.Row(
                controls=[
                    ft.Text(artist, size=12, color=TEXT_MUTED, max_lines=1),
                    ft.Text("•", size=12, color=TEXT_MUTED),
                    ft.Text(version, size=11, color=TEXT_MUTED),
                    ft.Text("•", size=12, color=TEXT_MUTED),
                    ft.Text(duration, size=11, color=TEXT_MUTED),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=4,
        expand=True,
    )

    choose_btn = ft.Container(
        data=f"select_track_{item_id}",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Elegir audio", size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ink=True,
        on_click=lambda _: on_select(item) if on_select else None,
    )

    return ft.Container(
        content=ft.Row(
            controls=[
                icon_container,
                info_col,
                choose_btn,
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=12,
    )


def build_search_view(
    initial_query: str = "",
    results: Optional[List[Dict[str, Any]]] = None,
    is_loading: bool = False,
    on_mode_change: Optional[Callable[[str], None]] = None,
    on_search: Optional[Callable[[str], None]] = None,
    on_select_track: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_error: Optional[Callable[[str, str], None]] = None,
) -> ft.Container:
    """
    Construye la vista de búsqueda por nombre (SearchView) para Coda.

    Incluye:
    - Cabecera contextual
    - Conmutador de modo (pestaña «Buscar por nombre» activa)
    - Campo de texto para términos de búsqueda con botón «Buscar»
    - Indicador de progreso / consulta en curso (`is_loading`)
    - Lista vertical de los 5 mejores resultados con tarjeta detallada y botón «Elegir audio»
    """
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
                "Encuentra tus pistas favoritas buscando por nombre, título o artista.",
                size=SUBTITLE_SIZE,
                color=TEXT_MUTED,
            ),
        ],
        spacing=6,
    )

    # 2. Conmutador de modo
    tab_pegar = ft.Container(
        data="paste_mode",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.LINK_ROUNDED, size=16, color=TEXT_MUTED),
                ft.Text("Pegar enlace", size=13, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda _: on_mode_change("paste") if on_mode_change else None,
    )

    tab_buscar = ft.Container(
        data="search_mode",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SEARCH_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Buscar por nombre", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, ACCENT_COLOR),
        border=ft.Border.all(1, ACCENT_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda _: on_mode_change("search") if on_mode_change else None,
    )

    mode_switcher = ft.Row(
        controls=[tab_pegar, tab_buscar],
        spacing=10,
    )

    # 3. Campo de texto para búsqueda y botón «Buscar»
    search_input = ft.TextField(
        value=initial_query,
        hint_text="Escribe el nombre de la canción o artista (ej: Daft Punk Get Lucky)...",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        bgcolor=SURFACE_COLOR,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        expand=True,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    def handle_search(_):
        query = (search_input.value or "").strip()
        if not query:
            if on_error:
                on_error("Término de búsqueda vacío", "Por favor ingresa el título o artista a buscar.")
            return

        if on_search:
            on_search(query)

    search_button = ft.Container(
        data="search_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SEARCH_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Buscar", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
        ink=True,
        on_click=handle_search,
    )

    input_card = ft.Container(
        content=ft.Row(
            controls=[search_input, search_button],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 4. Sección de resultados o estado de carga
    content_area_controls = []

    if is_loading:
        content_area_controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(color=ACCENT_COLOR, width=36, height=36),
                        ft.Text("Buscando las mejores coincidencias...", size=13, color=TEXT_MUTED),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=ft.Padding.symmetric(vertical=40),
                alignment=ft.Alignment.CENTER,
            )
        )
    elif results:
        result_cards = [_build_result_card(item, on_select=on_select_track) for item in results[:5]]
        content_area_controls.append(
            ft.Column(
                controls=[
                    ft.Text(
                        f"Mejores resultados ({len(result_cards)} encontrados):",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY,
                    ),
                    ft.Column(controls=result_cards, spacing=8),
                ],
                spacing=12,
            )
        )

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
                *content_area_controls,
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
