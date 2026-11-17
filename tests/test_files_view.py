from pathlib import Path
from typing import Any, List
import pytest
import flet as ft

from ui.gui.views.files_view import build_files_view


def test_build_files_view_returns_container():
    view = build_files_view()
    assert isinstance(view, ft.Container)


def test_build_files_view_empty_state(tmp_path: Path):
    new_download_called = []

    def on_new_download():
        new_download_called.append(True)

    view = build_files_view(downloads_dir=tmp_path, on_new_download=on_new_download)

    texts: List[str] = []

    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)
        if hasattr(ctrl, "rows") and ctrl.rows:
            for row in ctrl.rows:
                if hasattr(row, "cells") and row.cells:
                    for cell in row.cells:
                        extract_texts(cell)
        if hasattr(ctrl, "columns") and ctrl.columns:
            for col in ctrl.columns:
                if hasattr(col, "label") and col.label:
                    extract_texts(col.label)

    extract_texts(view)

    assert any("Archivos descargados" in t or "Archivos" in t for t in texts)
    assert any("No hay archivos descargados" in t or "vacía" in t.lower() for t in texts)
    assert any("0 descargas" in t or "0 archivo" in t for t in texts)
    assert any("Nueva descarga" in t for t in texts)


def test_build_files_view_with_files(tmp_path: Path):
    # Create test audio files
    (tmp_path / "Queen - Bohemian Rhapsody.mp3").write_bytes(b"A" * 1024 * 1024)
    (tmp_path / "Daft Punk - Get Lucky.m4a").write_bytes(b"B" * 1024 * 512)

    open_folder_called = []
    new_download_called = []

    def on_open_folder():
        open_folder_called.append(True)

    def on_new_download():
        new_download_called.append(True)

    view = build_files_view(
        downloads_dir=tmp_path,
        on_open_folder=on_open_folder,
        on_new_download=on_new_download,
    )

    texts: List[str] = []

    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)
        if hasattr(ctrl, "rows") and ctrl.rows:
            for row in ctrl.rows:
                if hasattr(row, "cells") and row.cells:
                    for cell in row.cells:
                        extract_texts(cell)
        if hasattr(ctrl, "columns") and ctrl.columns:
            for col in ctrl.columns:
                if hasattr(col, "label") and col.label:
                    extract_texts(col.label)

    extract_texts(view)

    # Check files summary
    assert any("2 descarga" in t or "2 archivo" in t for t in texts)
    assert any("Bohemian Rhapsody" in t for t in texts)
    assert any("Get Lucky" in t for t in texts)
    assert any("MP3" in t for t in texts)
    assert any("M4A" in t for t in texts)

    # Check table column titles
    assert any("Archivo" in t for t in texts)
    assert any("Tipo" in t or "Formato" in t for t in texts)
    assert any("Duración" in t or "Tamaño" in t for t in texts)
    assert any("Estado" in t for t in texts)

    # Check buttons
    open_btn = None
    new_btn = None

    def find_buttons(ctrl):
        nonlocal open_btn, new_btn
        if hasattr(ctrl, "data") and ctrl.data == "open_folder_btn":
            open_btn = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "new_download_btn":
            new_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_buttons(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_buttons(child)

    find_buttons(view)
    assert open_btn is not None
    assert new_btn is not None

    open_btn.on_click(None)
    assert len(open_folder_called) == 1

    new_btn.on_click(None)
    assert len(new_download_called) == 1


def test_build_files_view_has_no_edit_or_delete_buttons(tmp_path: Path):
    (tmp_path / "Track.mp3").write_bytes(b"X" * 100)
    view = build_files_view(downloads_dir=tmp_path)

    # Intangibilidad de archivos: no debe existir ningún botón de borrado, eliminación o edición
    texts: List[str] = []

    def extract_texts(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value).lower())
        if hasattr(ctrl, "tooltip") and ctrl.tooltip:
            texts.append(str(ctrl.tooltip).lower())
        if hasattr(ctrl, "content") and ctrl.content:
            extract_texts(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_texts(child)

    extract_texts(view)
    assert not any("eliminar" in t for t in texts)
    assert not any("borrar" in t for t in texts)
    assert not any("editar" in t for t in texts)
    assert not any("renombrar" in t for t in texts)
