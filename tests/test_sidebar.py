import flet as ft
import pytest

from ui.gui.views.sidebar import build_sidebar


def test_build_sidebar_structure_and_controls():
    sidebar = build_sidebar(current_section="inicio", queue_count=0)
    assert isinstance(sidebar, ft.Container)
    # Check width approximately 196px as specified (~196px)
    assert sidebar.width == 196

    # Verify presence of CODA logo text
    # Let's inspect controls recursively or find texts
    texts = []
    
    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(ctrl.value)
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)

    extract_texts(sidebar)
    
    assert any("CODA" in t for t in texts)
    assert any("TU ESPACIO" in t for t in texts)
    assert any("Inicio" in t for t in texts)
    assert any("Descargas" in t for t in texts)
    assert any("Archivos" in t for t in texts)
    assert any("Solo descargas" in t for t in texts)
    assert any("CODA · v1.0" in t for t in texts)


def test_build_sidebar_queue_count_badge():
    # When queue_count > 0, the badge should show the count
    sidebar_with_badge = build_sidebar(current_section="descargas", queue_count=3)
    texts = []
    
    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(ctrl.value)
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)

    extract_texts(sidebar_with_badge)
    assert "3" in texts


def test_build_sidebar_callbacks():
    clicked_sections = []

    def on_nav(section: str):
        clicked_sections.append(section)

    sidebar = build_sidebar(
        current_section="inicio",
        queue_count=0,
        on_navigate=on_nav,
    )
    
    # Check that navigation buttons invoke the callback
    # Find navigation buttons
    buttons = []
    
    def extract_buttons(ctrl):
        if hasattr(ctrl, "data") and ctrl.data in ("inicio", "descargas", "archivos"):
            buttons.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            extract_buttons(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_buttons(child)

    extract_buttons(sidebar)
    assert len(buttons) == 3

    # Simulate clicks
    for btn in buttons:
        if btn.on_click:
            btn.on_click(None)

    assert "inicio" in clicked_sections
    assert "descargas" in clicked_sections
    assert "archivos" in clicked_sections
