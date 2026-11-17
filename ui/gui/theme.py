import flet as ft

# Paleta cromática moderna y refinada de Coda (Studio Dark)
BG_DARK = "#0E0F12"          # Carbón profundo con matiz acústico
SURFACE_COLOR = "#16181D"    # Superficie elevada con claro contraste
SURFACE_HOVER = "#1E2129"    # Superficie en estado interactivo/hover
ACCENT_COLOR = "#E24A4A"     # Carmín acústico característico de Coda
ACCENT_LIGHT = "#FF5C5C"     # Realce del acento para foco y contraste
TEXT_PRIMARY = "#FFFFFF"     # Blanco óptico de máxima legibilidad
TEXT_MUTED = "#8E929E"       # Gris medio balanceado (no azulado opaco)
BORDER_COLOR = "#242731"     # Borde sutil y limpio (1px de separación)

# Radios de curvatura coherentes
RADIUS_CONTAINER = 12
RADIUS_BUTTON = 8
RADIUS_BADGE = 4

# Escala tipográfica armónica
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
        font_family="Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif",
    )

