from pathlib import Path
from typing import Any, List
import pytest
import flet as ft

from ui.gui.views.home_view import build_home_view
from utils.validator import clean_mixed_url


def test_clean_mixed_url_logic():
    # Pure video url without list
    url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    clean1, pruned1 = clean_mixed_url(url1)
    assert clean1 == url1
    assert pruned1 is False

    # Mixed video url with list=RD...
    url2 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&index=1"
    clean2, pruned2 = clean_mixed_url(url2)
    assert "list=" not in clean2
    assert "dQw4w9WgXcQ" in clean2
    assert pruned2 is True

    # YouTube Music mixed URL
    url3 = "https://music.youtube.com/watch?v=abc12345678&list=RDAMVMabc12345678"
    clean3, pruned3 = clean_mixed_url(url3)
    assert "list=" not in clean3
    assert "abc12345678" in clean3
    assert pruned3 is True

    # Pure playlist URL (not pruned)
    url4 = "https://www.youtube.com/playlist?list=PL1234567890"
    clean4, pruned4 = clean_mixed_url(url4)
    assert clean4 == url4
    assert pruned4 is False


def test_build_home_view_returns_container():
    view = build_home_view()
    assert isinstance(view, ft.Container)


def test_build_home_view_contains_expected_texts():
    view = build_home_view()

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

    # Cabecera
    assert any("Descarga tu música" in t for t in texts)
    # Conmutador de modo
    assert any("Pegar enlace" in t for t in texts)
    assert any("Buscar por nombre" in t for t in texts)
    # Botones
    assert any("Pegar" in t for t in texts)
    assert any("Analizar enlace" in t for t in texts)
    # Formatos soportados
    assert any("MP3" in t for t in texts)
    # Barra inferior informativa / destino
    assert any("downloads" in t.lower() or "destino" in t.lower() or "guardan" in t.lower() for t in texts)
    # Sección de recientes
    assert any("Descargas recientes" in t for t in texts)


def test_build_home_view_mode_switch_callback():
    switched_modes: List[str] = []

    def on_mode_change(mode: str):
        switched_modes.append(mode)

    view = build_home_view(on_mode_change=on_mode_change)

    search_tab_btn = None

    def find_tab(ctrl):
        nonlocal search_tab_btn
        if hasattr(ctrl, "data") and ctrl.data == "search_mode":
            search_tab_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_tab(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_tab(child)

    find_tab(view)
    assert search_tab_btn is not None
    if search_tab_btn.on_click:
        search_tab_btn.on_click(None)

    assert "search" in switched_modes


def test_build_home_view_validation_empty_url_triggers_error():
    modal_errors = []

    def on_error(title: str, msg: str):
        modal_errors.append((title, msg))

    analyzed = []

    def on_analyze(url: str):
        analyzed.append(url)

    view = build_home_view(on_analyze=on_analyze, on_error=on_error)

    url_field = None
    analyze_btn = None

    def find_controls(ctrl):
        nonlocal url_field, analyze_btn
        if isinstance(ctrl, ft.TextField):
            url_field = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "analyze_btn":
            analyze_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_controls(child)

    find_controls(view)
    assert url_field is not None
    assert analyze_btn is not None

    # Empty URL
    url_field.value = ""
    analyze_btn.on_click(None)

    assert len(modal_errors) == 1
    assert len(analyzed) == 0


def test_build_home_view_validation_invalid_url_triggers_error():
    modal_errors = []

    def on_error(title: str, msg: str):
        modal_errors.append((title, msg))

    analyzed = []

    def on_analyze(url: str):
        analyzed.append(url)

    view = build_home_view(on_analyze=on_analyze, on_error=on_error)

    url_field = None
    analyze_btn = None

    def find_controls(ctrl):
        nonlocal url_field, analyze_btn
        if isinstance(ctrl, ft.TextField):
            url_field = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "analyze_btn":
            analyze_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_controls(child)

    find_controls(view)
    # Invalid non-youtube URL
    url_field.value = "https://example.com/not-youtube"
    analyze_btn.on_click(None)

    assert len(modal_errors) == 1
    assert len(analyzed) == 0


def test_build_home_view_prunes_mixed_url_on_analyze():
    analyzed = []

    def on_analyze(url: str):
        analyzed.append(url)

    view = build_home_view(on_analyze=on_analyze)

    url_field = None
    analyze_btn = None

    def find_controls(ctrl):
        nonlocal url_field, analyze_btn
        if isinstance(ctrl, ft.TextField):
            url_field = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "analyze_btn":
            analyze_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_controls(child)

    find_controls(view)
    # Mixed URL with &list=RD...
    url_field.value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ"
    analyze_btn.on_click(None)

    assert len(analyzed) == 1
    assert "list=" not in analyzed[0]
    assert "dQw4w9WgXcQ" in analyzed[0]


def test_build_home_view_recent_downloads_table(tmp_path: Path):
    # Create sample files in tmp_path
    f1 = tmp_path / "Mi Cancion.mp3"
    f1.write_bytes(b"A" * 1024)

    view = build_home_view(downloads_dir=tmp_path)

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
    assert any("Mi Cancion.mp3" in t for t in texts)
