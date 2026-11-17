from typing import Callable, Optional
import flet as ft

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
    SUBTITLE_SIZE,
    META_SIZE,
)


def _build_nav_item(
    title: str,
    icon: str,
    section_id: str,
    is_active: bool,
    badge_count: int = 0,
    on_click: Optional[Callable[[str], None]] = None,
) -> ft.Container:
    """Construye un botón de navegación del sidebar con estilo visual según estado activo."""
    bg_color = ft.Colors.with_opacity(0.12, ACCENT_COLOR) if is_active else ft.Colors.TRANSPARENT
    text_color = TEXT_PRIMARY if is_active else TEXT_MUTED
    icon_color = ACCENT_COLOR if is_active else TEXT_MUTED

    content_controls = [
        ft.Icon(icon, color=icon_color, size=18),
        ft.Text(title, color=text_color, size=SUBTITLE_SIZE, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500),
    ]

    if badge_count > 0:
        content_controls.append(
            ft.Container(
                content=ft.Text(str(badge_count), size=META_SIZE, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                bgcolor=ACCENT_COLOR,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                alignment=ft.Alignment.CENTER,
            )
        )

    return ft.Container(
        data=section_id,
        content=ft.Row(
            controls=content_controls,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        bgcolor=bg_color,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.25, ACCENT_COLOR) if is_active else ft.Colors.TRANSPARENT),
        ink=True,
        on_click=lambda _: on_click(section_id) if on_click else None,
    )


def build_sidebar(
    current_section: str = "inicio",
    queue_count: int = 0,
    on_navigate: Optional[Callable[[str], None]] = None,
) -> ft.Container:
    """
    Construye la barra de navegación lateral fija para la interfaz de Coda.

    Incluye:
    - Logo CODA con acento rojo
    - Sección «TU ESPACIO»
    - Navegación: Inicio, Descargas (con badge opcional), Archivos
    - Tarjeta informativa: «Solo descargas. Sin reproductor integrado.»
    - Versión de la aplicación: «CODA · v1.0»
    """
    # 1. Cabecera con Logo
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    width=10,
                    height=20,
                    bgcolor=ACCENT_COLOR,
                    border_radius=ft.BorderRadius.all(2),
                ),
                ft.Text("CODA", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.Padding.only(left=8, top=16, bottom=16),
    )

    # 2. Etiqueta de sección
    section_label = ft.Container(
        content=ft.Text(
            "TU ESPACIO",
            size=META_SIZE,
            color=TEXT_MUTED,
            weight=ft.FontWeight.BOLD,
        ),
        padding=ft.Padding.only(left=8, bottom=8, top=8),
    )

    # 3. Botones de navegación
    nav_inicio = _build_nav_item(
        title="Inicio",
        icon=ft.Icons.HOME_ROUNDED,
        section_id="inicio",
        is_active=(current_section.lower() == "inicio"),
        on_click=on_navigate,
    )

    nav_descargas = _build_nav_item(
        title="Descargas",
        icon=ft.Icons.DOWNLOAD_ROUNDED,
        section_id="descargas",
        is_active=(current_section.lower() == "descargas"),
        badge_count=queue_count,
        on_click=on_navigate,
    )

    nav_archivos = _build_nav_item(
        title="Archivos",
        icon=ft.Icons.FOLDER_ROUNDED,
        section_id="archivos",
        is_active=(current_section.lower() == "archivos"),
        on_click=on_navigate,
    )

    # 4. Tarjeta informativa inferior
    info_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=TEXT_MUTED, size=16),
                        ft.Text("Aviso", size=11, color=TEXT_MUTED, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=6,
                ),
                ft.Text(
                    "Solo descargas. Sin reproductor integrado.",
                    size=10,
                    color=TEXT_MUTED,
                ),
            ],
            spacing=4,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=10,
    )

    # 5. Versión
    footer_version = ft.Container(
        content=ft.Text(
            "CODA · v1.0",
            size=META_SIZE,
            color=TEXT_MUTED,
            weight=ft.FontWeight.W_400,
        ),
        alignment=ft.Alignment.CENTER_LEFT,
        padding=ft.Padding.only(left=8, top=8, bottom=16),
    )

    # Contenedor principal del Sidebar
    return ft.Container(
        width=196,
        bgcolor=BG_DARK,
        border=ft.Border.only(right=ft.BorderSide(1, BORDER_COLOR)),
        padding=ft.Padding.symmetric(horizontal=12),
        content=ft.Column(
            controls=[
                header,
                section_label,
                nav_inicio,
                nav_descargas,
                nav_archivos,
                ft.Container(expand=True),  # Espaciador flexible
                info_card,
                footer_version,
            ],
            spacing=6,
            expand=True,
        ),
    )
