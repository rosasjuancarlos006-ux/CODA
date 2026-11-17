import flet as ft

# Paleta cromática oficial de Coda (Diseño Figma)
BG_DARK = "#121214"
SURFACE_COLOR = "#1A1A1E"
ACCENT_COLOR = "#E24A4A"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#8E8E93"
BORDER_COLOR = "#2C2C30"

# Radios de curvatura
RADIUS_CONTAINER = 12
RADIUS_BUTTON = 8
RADIUS_BADGE = 4

# Escala tipográfica
TITLE_SIZE = 24
SUBTITLE_SIZE = 14
META_SIZE = 11


def build_coda_theme() -> ft.Theme:
    """Construye y retorna el tema visual oscuro configurado para Coda."""
    return ft.Theme(
        color_scheme_seed=ACCENT_COLOR,
        color_scheme=ft.ColorScheme(
            surface=SURFACE_COLOR,
            primary=ACCENT_COLOR,
            on_primary=TEXT_PRIMARY,
            on_surface=TEXT_PRIMARY,
            outline=BORDER_COLOR,
        ),
    )
