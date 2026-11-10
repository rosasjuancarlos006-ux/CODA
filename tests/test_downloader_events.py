from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from core.events import DownloadPhase, ProgressEvent
import core.downloader as downloader


class TestDownloaderEvents:
    def test_downloader_does_not_import_rich(self):
        """Verifica que el motor de descarga no importe ni exponga rich (Principio 3)."""
        exposed_names = [name for name in dir(downloader) if not name.startswith("_")]
        assert "rich" not in exposed_names
        assert "console" not in exposed_names

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("core.downloader.yt_dlp.YoutubeDL")
    @patch("core.downloader.write_id3_metadata", return_value=True)
    def test_download_audio_emits_progress_events(self, mock_meta, mock_ydl_cls, mock_ffmpeg, tmp_path: Path):
        """Verifica que download_audio_from_youtube emita ProgressEvent en sus fases."""
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Canción Test",
            "uploader": "Artista Test",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg"
        }

        # Simular que el archivo de audio se crea en el directorio
        audio_file = tmp_path / "Canción Test.mp3"
        audio_file.write_text("dummy mp3")

        events = []
        def progress_listener(evt: ProgressEvent):
            events.append(evt)

        result = downloader.download_audio_from_youtube(
            query="test query",
            output_dir=tmp_path,
            audio_format="mp3",
            on_progress=progress_listener
        )

        assert result["success"] is True
        assert len(events) >= 3

        phases = [e.phase for e in events]
        assert DownloadPhase.PREPARING in phases
        assert DownloadPhase.METADATA in phases
        assert DownloadPhase.COMPLETED in phases

        for e in events:
            assert isinstance(e, ProgressEvent)

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("core.downloader.yt_dlp.YoutubeDL")
    @patch("core.downloader.download_audio_from_youtube")
    def test_download_playlist_emits_progress_events(self, mock_download_single, mock_ydl_cls, mock_ffmpeg, tmp_path: Path):
        """Verifica que download_playlist emita ProgressEvent con current_item y total_items."""
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Mi Playlist",
            "entries": [
                {"id": "v1", "title": "Track 1", "url": "https://youtube.com/watch?v=v1"},
                {"id": "v2", "title": "Track 2", "url": "https://youtube.com/watch?v=v2"}
            ]
        }
        mock_download_single.return_value = {
            "success": True,
            "title": "Track",
            "uploader": "Artist",
            "mp3_path": str(tmp_path / "track.mp3")
        }

        events = []
        def progress_listener(evt: ProgressEvent):
            events.append(evt)

        result = downloader.download_playlist(
            playlist_url="https://youtube.com/playlist?list=123",
            output_dir=tmp_path,
            on_progress=progress_listener
        )

        assert result["success"] is True
        assert len(events) > 0
        for e in events:
            assert isinstance(e, ProgressEvent)
            assert e.total_items == 2
            assert e.current_item in (1, 2)
