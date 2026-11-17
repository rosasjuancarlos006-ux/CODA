from typing import Any, Dict, List
import pytest
import flet as ft

from ui.gui.views.search_view import build_search_view


def test_build_search_view_returns_container():
    view = build_search_view()
    assert isinstance(view, ft.Container)


def test_build_search_view_initial_elements():
    view = build_search_view()

    texts: List[str] = []

    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)

    extract_texts(view)

    assert any("Buscar" in t for t in texts)
    assert any("Pegar enlace" in t for t in texts)
    assert any("Buscar por nombre" in t for t in texts)


def test_build_search_view_search_callback_and_empty_validation():
    searched_queries = []
    modal_errors = []

    def on_search(q: str):
        searched_queries.append(q)

    def on_error(title: str, msg: str):
        modal_errors.append((title, msg))

    view = build_search_view(on_search=on_search, on_error=on_error)

    search_input = None
    search_btn = None

    def find_controls(ctrl):
        nonlocal search_input, search_btn
        if isinstance(ctrl, ft.TextField):
            search_input = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "search_btn":
            search_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_controls(child)

    find_controls(view)
    assert search_input is not None
    assert search_btn is not None

    # Empty search query -> triggers modal error
    search_input.value = ""
    search_btn.on_click(None)
    assert len(modal_errors) == 1
    assert len(searched_queries) == 0

    # Valid search query -> triggers search callback
    search_input.value = "Daft Punk Get Lucky"
    search_btn.on_click(None)
    assert len(searched_queries) == 1
    assert searched_queries[0] == "Daft Punk Get Lucky"


def test_build_search_view_displays_5_results_with_cards_and_select_callback():
    sample_results: List[Dict[str, Any]] = [
        {
            "id": f"id_{i}",
            "title": f"Canción {i}",
            "artist": f"Artista {i}",
            "version": "Audio oficial" if i % 2 == 0 else "Video",
            "duration_str": f"03:4{i}",
            "thumbnail_url": None,
            "url": f"https://www.youtube.com/watch?v=mock_{i}",
        }
        for i in range(1, 6)
    ]

    selected_tracks = []

    def on_select(item: Dict[str, Any]):
        selected_tracks.append(item)

    view = build_search_view(results=sample_results, on_select_track=on_select)

    texts: List[str] = []

    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)

    extract_texts(view)

    # Check that all 5 results are present
    for i in range(1, 6):
        assert any(f"Canción {i}" in t for t in texts)
        assert any(f"Artista {i}" in t for t in texts)

    assert any("Elegir audio" in t for t in texts)

    # Find the first "Elegir audio" button
    select_buttons = []

    def find_select_buttons(ctrl):
        if hasattr(ctrl, "data") and str(ctrl.data).startswith("select_track_"):
            select_buttons.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            find_select_buttons(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_select_buttons(child)

    find_select_buttons(view)
    assert len(select_buttons) == 5

    # Click first button
    select_buttons[0].on_click(None)
    assert len(selected_tracks) == 1
    assert selected_tracks[0]["title"] == "Canción 1"


def test_build_search_view_loading_state():
    view = build_search_view(is_loading=True)

    progress_rings = []

    def find_rings(ctrl):
        if isinstance(ctrl, ft.ProgressRing):
            progress_rings.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            find_rings(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_rings(child)

    find_rings(view)
    assert len(progress_rings) >= 1
