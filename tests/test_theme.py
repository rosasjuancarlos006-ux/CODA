import pytest

def test_theme_constants_and_tokens():
    """
    Verifica que ui.gui.theme defina las constantes cromáticas, radios y escala
    tipográfica conforme al plan y al diseño Figma 'CODA'.
    """
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

    assert BG_DARK.startswith("#")
    assert SURFACE_COLOR.startswith("#")
    assert ACCENT_COLOR.startswith("#")
    assert TEXT_PRIMARY.startswith("#")
    assert TEXT_MUTED.startswith("#")
    assert BORDER_COLOR.startswith("#")

    assert RADIUS_CONTAINER > 0
    assert RADIUS_BUTTON > 0
    assert RADIUS_BADGE > 0

    assert TITLE_SIZE > SUBTITLE_SIZE > META_SIZE


def test_build_coda_theme_returns_flet_theme():
    """
    Verifica que build_coda_theme retorne una instancia configurada de Theme de flet.
    """
    import flet as ft
    from ui.gui.theme import build_coda_theme, BG_DARK

    theme = build_coda_theme()
    assert isinstance(theme, ft.Theme)
    assert theme.color_scheme_seed is not None or theme.color_scheme is not None
