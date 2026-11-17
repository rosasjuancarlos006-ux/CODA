import logging
from typing import Any, Callable, Dict, Optional
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


def build_options_view(
    track_info: Optional[Dict[str, Any]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
    on_start_download: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> ft.Container:
    """
    Construye la pantalla de Opciones de descarga (OptionsView) para Coda.

    Incluye:
    - Cabecera y tarjeta de la pista seleccionada (título, artista/canal, duración)
    - Radio buttons de plataforma (YouTube / YouTube Music)
    - Radio buttons de formato (MP3 / M4A / OPUS)
    - Indicador de calidad automática (Máxima fidelidad disponible)
    - Campo numérico condicional de límite de playlist (solo si is_playlist=True)
    - Destino de descarga (`downloads/`)
    - Botones «Cancelar» / «Iniciar descarga»
    """
    info = track_info or {}
    title = info.get("title", "Canción seleccionada")
    artist = info.get("artist") or info.get("channel") or info.get("uploader") or "Artista / Canal"
    duration = info.get("duration_str", "--:--")
    is_playlist = bool(info.get("is_playlist", False))
    url = info.get("url") or info.get("url_or_query") or ""

    # 1. Cabecera
    header_col = ft.Column(
        controls=[
            ft.Text(
                "Opciones de descarga",
                size=TITLE_SIZE,
                weight=ft.FontWeight.BOLD,
                color=TEXT_PRIMARY,
            ),
            ft.Text(
                "Personaliza el formato, plataforma y opciones de guardado antes de descargar.",
                size=SUBTITLE_SIZE,
                color=TEXT_MUTED,
            ),
        ],
        spacing=6,
    )

    # 2. Tarjeta con resumen de la pista seleccionada
    track_summary_card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.QUEUE_MUSIC_ROUNDED if is_playlist else ft.Icons.MUSIC_NOTE_ROUNDED,
                        color=ACCENT_COLOR,
                        size=28,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.12, ACCENT_COLOR),
                    border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
                    width=54,
                    height=54,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, max_lines=1),
                                ft.Container(
                                    content=ft.Text(
                                        "Playlist" if is_playlist else "Pista individual",
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_PRIMARY,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.15, ACCENT_COLOR if is_playlist else TEXT_MUTED),
                                    border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(artist, size=12, color=TEXT_MUTED),
                                ft.Text("•", size=12, color=TEXT_MUTED),
                                ft.Text(f"Duración: {duration}", size=12, color=TEXT_MUTED),
                            ],
                            spacing=6,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 3. RadioGroup de Plataforma
    platform_group = ft.RadioGroup(
        data="platform_radios",
        value=info.get("platform", "youtube"),
        content=ft.Row(
            controls=[
                ft.Radio(value="youtube", label="YouTube (General)", fill_color=ACCENT_COLOR),
                ft.Radio(value="youtube_music", label="YouTube Music (Oficial)", fill_color=ACCENT_COLOR),
            ],
            spacing=20,
        ),
    )

    platform_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Plataforma de origen", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                platform_group,
            ],
            spacing=8,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 4. RadioGroup de Formato de Audio
    format_group = ft.RadioGroup(
        data="format_radios",
        value=info.get("audio_format", "mp3"),
        content=ft.Row(
            controls=[
                ft.Radio(value="mp3", label="MP3 (320 kbps)", fill_color=ACCENT_COLOR),
                ft.Radio(value="m4a", label="M4A (AAC)", fill_color=ACCENT_COLOR),
                ft.Radio(value="opus", label="OPUS (Original)", fill_color=ACCENT_COLOR),
            ],
            spacing=20,
        ),
    )

    format_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Formato de audio de salida", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(
                            content=ft.Text("Calidad: Automática (Máxima)", size=10, color=TEXT_MUTED),
                            bgcolor=ft.Colors.with_opacity(0.08, TEXT_PRIMARY),
                            border_radius=ft.BorderRadius.all(RADIUS_BADGE),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                format_group,
            ],
            spacing=8,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
        padding=16,
    )

    # 5. Campo de Límite de Playlist (Solo si es Playlist)
    limit_input = ft.TextField(
        data="playlist_limit_input",
        value=str(info.get("playlist_limit", "")) if info.get("playlist_limit") else "",
        hint_text="Dejar vacío o 0 para descargar todas las canciones",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=12),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        bgcolor=SURFACE_COLOR,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        expand=True,
    )

    playlist_limit_section = None
    if is_playlist:
        playlist_limit_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Límite de pistas a descargar (Opcional)",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY,
                    ),
                    limit_input,
                ],
                spacing=8,
            ),
            bgcolor=SURFACE_COLOR,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=ft.BorderRadius.all(RADIUS_CONTAINER),
            padding=16,
        )

    # 6. Botones de acción («Cancelar» / «Iniciar descarga»)
    cancel_btn = ft.Container(
        key="options_cancel_btn",
        data="cancel_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CLOSE_ROUNDED, size=16, color=TEXT_MUTED),
                ft.Text("Cancelar", size=13, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
        ink=True,
        on_click=lambda _: on_cancel() if on_cancel else None,
    )

    def handle_confirm(_):
        limit_val: Optional[int] = None
        raw_limit = (limit_input.value or "").strip()
        if raw_limit.isdigit() and int(raw_limit) > 0:
            limit_val = int(raw_limit)

        chosen_options = {
            "title": title,
            "artist": artist,
            "duration_str": duration,
            "url": url,
            "is_playlist": is_playlist,
            "platform": platform_group.value or "youtube",
            "audio_format": format_group.value or "mp3",
            "quality": "best",
            "playlist_limit": limit_val,
        }
        if on_start_download:
            on_start_download(chosen_options)

    start_btn = ft.Container(
        key="options_start_download_btn",
        data="start_download_btn",
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=16, color=TEXT_PRIMARY),
                ft.Text("Iniciar descarga", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ACCENT_COLOR,
        border_radius=ft.BorderRadius.all(RADIUS_BUTTON),
        padding=ft.Padding.symmetric(horizontal=22, vertical=10),
        ink=True,
        on_click=handle_confirm,
    )

    actions_row = ft.Row(
        controls=[cancel_btn, start_btn],
        alignment=ft.MainAxisAlignment.END,
        spacing=12,
    )

    # 7. Barra inferior informativa con destino
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
                    "Calidad automática: se obtiene la mejor tasa de bits de la fuente.",
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

    form_controls = [
        header_col,
        track_summary_card,
        platform_section,
        format_section,
    ]
    if playlist_limit_section:
        form_controls.append(playlist_limit_section)

    form_controls.append(actions_row)
    form_controls.append(ft.Container(expand=True))
    form_controls.append(footer_bar)

    return ft.Container(
        content=ft.Column(
            controls=form_controls,
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.Padding.all(24),
        expand=True,
    )
