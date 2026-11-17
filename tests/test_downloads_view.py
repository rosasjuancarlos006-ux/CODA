from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import flet as ft

from core.events import DownloadPhase, ProgressEvent
from core.queue_manager import QueueItem, QueueItemStatus
from ui.gui.views.downloads_view import build_downloads_view


def test_build_downloads_view_returns_container():
    view = build_downloads_view()
    assert isinstance(view, ft.Container)


def test_build_downloads_view_empty_state_when_no_active_download():
    view = build_downloads_view(active_item=None, progress_event=None)

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

    assert any("Descargas" in t for t in texts)
    assert any("No hay descargas activas" in t or "vacía" in t.lower() for t in texts)


def test_build_downloads_view_active_download_card_with_metrics():
    active_item = QueueItem(
        item_id="item-1",
        title="Cancion Activa",
        url_or_query="https://youtube.com/watch?v=123",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="03:45",
        status=QueueItemStatus.ACTIVE,
    )
    progress_event = ProgressEvent(
        phase=DownloadPhase.DOWNLOADING,
        percentage=65.5,
        speed_bytes_sec=1024 * 1024 * 2.5,  # 2.5 MB/s
        eta_seconds=15,
        item_title="Cancion Activa",
    )

    view = build_downloads_view(active_item=active_item, progress_event=progress_event)

    texts: List[str] = []
    progress_bars: List[ft.ProgressBar] = []

    def extract_controls(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if isinstance(ctrl, ft.ProgressBar):
            progress_bars.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            extract_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_controls(child)

    extract_controls(view)

    # Title & Phase badge
    assert any("Cancion Activa" in t for t in texts)
    assert any("Transferencia" in t or "Descargando" in t for t in texts)
    assert any("65.5%" in t or "65%" in t or "66%" in t for t in texts)

    # Metrics
    assert any("MB/s" in t or "2.5" in t for t in texts)
    assert any("15s" in t or "00:15" in t or "15 seg" in t for t in texts)
    assert any("downloads" in t.lower() for t in texts)

    # Progress bar value should be ~0.655
    assert len(progress_bars) >= 1
    assert progress_bars[0].value is not None
    assert pytest.approx(progress_bars[0].value, 0.01) == 0.655


def test_build_downloads_view_degradation_when_metrics_none():
    active_item = QueueItem(
        item_id="item-2",
        title="Cancion Convirtiendose",
        url_or_query="https://youtube.com/watch?v=456",
        platform="youtube_music",
        audio_format="opus",
        quality="best",
        playlist_limit=0,
        duration_str="04:10",
        status=QueueItemStatus.ACTIVE,
    )
    progress_event = ProgressEvent(
        phase=DownloadPhase.CONVERTING,
        percentage=None,
        speed_bytes_sec=None,
        eta_seconds=None,
    )

    view = build_downloads_view(active_item=active_item, progress_event=progress_event)

    texts: List[str] = []
    progress_bars: List[ft.ProgressBar] = []
    progress_rings: List[ft.ProgressRing] = []

    def extract_controls(ctrl):
        if hasattr(ctrl, "value") and ctrl.value:
            texts.append(str(ctrl.value))
        if isinstance(ctrl, ft.ProgressBar):
            progress_bars.append(ctrl)
        if isinstance(ctrl, ft.ProgressRing):
            progress_rings.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            extract_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                extract_controls(child)

    extract_controls(view)

    assert any("Conversión" in t or "Procesando" in t for t in texts)
    assert len(progress_bars) >= 1 or len(progress_rings) >= 1
    if progress_bars:
        assert progress_bars[0].value is None


def test_build_downloads_view_cancel_active_download_callback():
    cancelled_ids = []

    def on_cancel(item_id: str):
        cancelled_ids.append(item_id)

    active_item = QueueItem(
        item_id="cancel-test-id",
        title="Pista a Cancelar",
        url_or_query="https://youtube.com",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="02:00",
        status=QueueItemStatus.ACTIVE,
    )

    view = build_downloads_view(active_item=active_item, on_cancel_active=on_cancel)

    cancel_btn = None

    def find_cancel(ctrl):
        nonlocal cancel_btn
        if hasattr(ctrl, "data") and ctrl.data == "cancel_active_btn":
            cancel_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_cancel(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_cancel(child)

    find_cancel(view)
    assert cancel_btn is not None
    cancel_btn.on_click(None)
    assert cancelled_ids == ["cancel-test-id"]


def test_build_downloads_view_queue_list_and_step_indicator():
    queue_items = [
        QueueItem(
            item_id="q-1",
            title="Segunda Cancion",
            url_or_query="https://youtube.com/watch?v=222",
            platform="youtube",
            audio_format="mp3",
            quality="best",
            playlist_limit=0,
            duration_str="03:00",
            status=QueueItemStatus.PENDING,
        ),
        QueueItem(
            item_id="q-2",
            title="Tercera Cancion",
            url_or_query="https://youtube.com/watch?v=333",
            platform="youtube_music",
            audio_format="m4a",
            quality="best",
            playlist_limit=0,
            duration_str="04:20",
            status=QueueItemStatus.PENDING,
        ),
    ]

    view = build_downloads_view(
        active_item=None,
        queue=queue_items,
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

    extract_texts(view)

    assert any("En cola de espera (2 canciones)" in t or "En cola de espera (2" in t for t in texts)
    assert any("Segunda Cancion" in t for t in texts)
    assert any("Tercera Cancion" in t for t in texts)
    assert any("MP3" in t for t in texts)
    assert any("M4A" in t for t in texts)

    assert any("Conexión lista" in t for t in texts)
    assert any("Descargando" in t for t in texts)
    assert any("Guardar archivo" in t for t in texts)


def test_build_downloads_view_queue_item_removal_callback():
    removed_ids = []

    def on_remove(item_id: str):
        removed_ids.append(item_id)

    queue_items = [
        QueueItem(
            item_id="remove-target-id",
            title="Cancion para borrar",
            url_or_query="https://youtube.com/watch?v=remove",
            platform="youtube",
            audio_format="opus",
            quality="best",
            playlist_limit=0,
            duration_str="02:50",
            status=QueueItemStatus.PENDING,
        )
    ]

    view = build_downloads_view(
        queue=queue_items,
        on_remove_from_queue=on_remove,
    )

    remove_buttons = []

    def find_remove_buttons(ctrl):
        if hasattr(ctrl, "data") and ctrl.data == "remove_queue_remove-target-id":
            remove_buttons.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            find_remove_buttons(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_remove_buttons(child)

    find_remove_buttons(view)
    assert len(remove_buttons) == 1
    remove_buttons[0].on_click(None)
    assert removed_ids == ["remove-target-id"]


def test_build_downloads_view_completed_success_state():
    completed_result = {
        "title": "Cancion Exitosa",
        "artist": "Artista Exitoso",
        "audio_format": "mp3",
        "duration_str": "03:15",
        "size_str": "7.5 MB",
        "file_path": Path("downloads/Cancion Exitosa.mp3"),
    }

    opened_folders = []
    new_downloads = []

    def on_open_folder():
        opened_folders.append(True)

    def on_new_download():
        new_downloads.append(True)

    # When queue is empty and last_completed is provided without an active item
    view = build_downloads_view(
        active_item=None,
        queue=[],
        completed_item=completed_result,
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

    extract_texts(view)

    assert any("Descarga exitosa" in t for t in texts)
    assert any("Cancion Exitosa" in t for t in texts)
    assert any("Artista Exitoso" in t for t in texts)
    assert any("7.5 MB" in t for t in texts)
    assert any("Abrir carpeta" in t for t in texts)
    assert any("Nueva descarga" in t for t in texts)

    # Find and trigger action buttons
    open_folder_btn = None
    new_download_btn = None

    def find_action_buttons(ctrl):
        nonlocal open_folder_btn, new_download_btn
        if hasattr(ctrl, "data") and ctrl.data == "open_folder_btn":
            open_folder_btn = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "new_download_btn":
            new_download_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_action_buttons(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_action_buttons(child)

    find_action_buttons(view)
    assert open_folder_btn is not None
    assert new_download_btn is not None

    open_folder_btn.on_click(None)
    assert len(opened_folders) == 1

    new_download_btn.on_click(None)
    assert len(new_downloads) == 1


def test_build_downloads_view_completed_state_suppressed_when_queue_pending():
    completed_result = {
        "title": "Cancion Exitosa",
        "artist": "Artista Exitoso",
        "audio_format": "mp3",
    }
    pending_item = QueueItem(
        item_id="next-id",
        title="Cancion Siguiente",
        url_or_query="https://youtube.com/watch?v=next",
        platform="youtube",
        audio_format="mp3",
        quality="best",
        playlist_limit=0,
        duration_str="02:40",
        status=QueueItemStatus.PENDING,
    )

    # If there are still pending items in queue, completed screen is suppressed in favor of queue
    view = build_downloads_view(
        active_item=None,
        queue=[pending_item],
        completed_item=completed_result,
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

    extract_texts(view)

    # Success screen suppressed because next queue item is waiting
    assert not any("Descarga exitosa" in t for t in texts)
    assert any("En cola de espera" in t for t in texts)
