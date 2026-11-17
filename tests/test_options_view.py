from typing import Any, Dict, List, Optional
import pytest
import flet as ft

from ui.gui.views.options_view import build_options_view


def test_build_options_view_returns_container():
    view = build_options_view(track_info={"title": "Test Title", "artist": "Test Artist"})
    assert isinstance(view, ft.Container)


def test_build_options_view_displays_track_information():
    track_info = {
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "duration_str": "05:55",
        "url": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
    }
    view = build_options_view(track_info=track_info)

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

    assert any("Bohemian Rhapsody" in t for t in texts)
    assert any("Queen" in t for t in texts)
    assert any("05:55" in t for t in texts)
    assert any("Opciones de descarga" in t for t in texts)
    assert any("Automática" in t or "automática" in t.lower() for t in texts)
    assert any("downloads" in t.lower() for t in texts)


def test_build_options_view_playlist_limit_field_visibility():
    # Individual video: playlist limit field should NOT be visible / or not present
    single_track = {"title": "Single", "is_playlist": False}
    view_single = build_options_view(track_info=single_track)

    limit_inputs_single = []

    def find_limit_inputs(ctrl, acc):
        if hasattr(ctrl, "data") and ctrl.data == "playlist_limit_input":
            if getattr(ctrl, "visible", True):
                acc.append(ctrl)
        if hasattr(ctrl, "content") and ctrl.content:
            find_limit_inputs(ctrl.content, acc)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_limit_inputs(child, acc)

    find_limit_inputs(view_single, limit_inputs_single)
    assert len(limit_inputs_single) == 0

    # Playlist: playlist limit field should BE present and visible
    playlist_track = {"title": "My Playlist", "is_playlist": True}
    view_playlist = build_options_view(track_info=playlist_track)

    limit_inputs_playlist = []
    find_limit_inputs(view_playlist, limit_inputs_playlist)
    assert len(limit_inputs_playlist) == 1


def test_build_options_view_cancel_callback():
    cancelled = []

    def on_cancel():
        cancelled.append(True)

    view = build_options_view(
        track_info={"title": "Test"},
        on_cancel=on_cancel,
    )

    cancel_btn = None

    def find_cancel(ctrl):
        nonlocal cancel_btn
        if hasattr(ctrl, "data") and ctrl.data == "cancel_btn":
            cancel_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_cancel(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_cancel(child)

    find_cancel(view)
    assert cancel_btn is not None
    cancel_btn.on_click(None)
    assert len(cancelled) == 1


def test_build_options_view_start_download_callback_collects_options():
    download_requests = []

    def on_start_download(options: Dict[str, Any]):
        download_requests.append(options)

    track_info = {
        "title": "Song Title",
        "artist": "Artist Name",
        "url": "https://www.youtube.com/watch?v=123",
        "duration_str": "03:30",
        "is_playlist": True,
    }

    view = build_options_view(
        track_info=track_info,
        on_start_download=on_start_download,
    )

    # Change platform, format, and limit
    platform_group = None
    format_group = None
    limit_input = None
    start_btn = None

    def find_form_controls(ctrl):
        nonlocal platform_group, format_group, limit_input, start_btn
        if hasattr(ctrl, "data") and ctrl.data == "platform_radios":
            platform_group = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "format_radios":
            format_group = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "playlist_limit_input":
            limit_input = ctrl
        if hasattr(ctrl, "data") and ctrl.data == "start_download_btn":
            start_btn = ctrl
        if hasattr(ctrl, "content") and ctrl.content:
            find_form_controls(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for child in ctrl.controls:
                find_form_controls(child)

    find_form_controls(view)
    assert platform_group is not None
    assert format_group is not None
    assert limit_input is not None
    assert start_btn is not None

    # Set values
    platform_group.value = "youtube_music"
    format_group.value = "m4a"
    limit_input.value = "10"

    start_btn.on_click(None)

    assert len(download_requests) == 1
    req = download_requests[0]
    assert req["platform"] == "youtube_music"
    assert req["audio_format"] == "m4a"
    assert req["playlist_limit"] == 10
    assert req["title"] == "Song Title"
    assert req["url"] == "https://www.youtube.com/watch?v=123"
