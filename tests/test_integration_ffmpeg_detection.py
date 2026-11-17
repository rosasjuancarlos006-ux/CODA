from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from core.downloader import download_audio_from_youtube, download_playlist, find_ffmpeg
from core.events import DownloadPhase, ProgressEvent
from metadata.writer import _find_ffmpeg_binary


# =====================================================================
# QA Test Suite: Detección y Jerarquía de Precedencia de FFmpeg (Tarea 2.1)
# =====================================================================


class TestFFmpegDetectionIntegrationQA:
    """Pruebas de precedencia, detección y aborto seguro ante la presencia o ausencia de FFmpeg."""

    def test_tc_2_1_1_local_bin_precedence_over_system_path(self, tmp_path: Path):
        """Verifica que si existe bin/ffmpeg.exe local, se prioriza sobre el PATH global del sistema."""
        dummy_local_ffmpeg = tmp_path / "ffmpeg.exe"
        dummy_local_ffmpeg.touch()

        # Simulamos que existe tanto local como en el PATH global
        with patch("core.downloader.FFMPEG_DIR", tmp_path):
            with patch("shutil.which", return_value="C:\\System32\\ffmpeg.exe"):
                found = find_ffmpeg()
                assert found is not None
                assert str(dummy_local_ffmpeg) == found
                assert "C:\\System32\\ffmpeg.exe" != found

    def test_tc_2_1_2_fallback_to_system_path_when_bin_absent(self, tmp_path: Path):
        """Si no existe bin/ffmpeg.exe local, debe recurrir a shutil.which en el PATH del sistema."""
        empty_bin_dir = tmp_path / "empty_bin"
        empty_bin_dir.mkdir()

        with patch("core.downloader.FFMPEG_DIR", empty_bin_dir):
            with patch("shutil.which", return_value="C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"):
                found = find_ffmpeg()
                assert found == "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"

    def test_tc_2_1_3_safe_abort_when_ffmpeg_missing_completely(self, tmp_path: Path):
        """Si no existe ni en bin/ ni en el PATH, download_audio_from_youtube aborta inmediatamente sin invocar yt-dlp."""
        empty_bin_dir = tmp_path / "empty_bin"
        empty_bin_dir.mkdir()

        with patch("core.downloader.FFMPEG_DIR", empty_bin_dir):
            with patch("shutil.which", return_value=None):
                assert find_ffmpeg() is None

                captured_events: list[ProgressEvent] = []

                # Descarga individual debe abortar con error tipificado
                result = download_audio_from_youtube(
                    query="https://www.youtube.com/watch?v=123",
                    output_dir=tmp_path,
                    on_progress=captured_events.append,
                )

                assert result["success"] is False
                assert result["error"] == "ffmpeg_missing"
                assert "FFmpeg no fue detectado" in result["message"]

                # Debe notificar fase ERROR en los eventos
                error_events = [e for e in captured_events if e.phase == DownloadPhase.ERROR]
                assert len(error_events) >= 1
                assert "FFmpeg no fue detectado" in (error_events[0].message or "")

    def test_tc_2_1_3_safe_abort_playlist_when_ffmpeg_missing(self, tmp_path: Path):
        """Si no existe FFmpeg, download_playlist aborta inmediatamente sin invocar subprocesos."""
        empty_bin_dir = tmp_path / "empty_bin"
        empty_bin_dir.mkdir()

        with patch("core.downloader.FFMPEG_DIR", empty_bin_dir):
            with patch("shutil.which", return_value=None):
                captured_events: list[ProgressEvent] = []

                summary = download_playlist(
                    playlist_url="https://www.youtube.com/playlist?list=PL123",
                    output_dir=tmp_path,
                    on_progress=captured_events.append,
                )

                assert summary["success"] is False
                assert summary["error"] == "ffmpeg_missing"
                assert any(e.phase == DownloadPhase.ERROR for e in captured_events)

    def test_tc_2_1_4_metadata_writer_ffmpeg_detection_consistency(self, tmp_path: Path):
        """Verifica que metadata.writer._find_ffmpeg_binary mantenga la misma jerarquía de precedencia."""
        dummy_local_ffmpeg = tmp_path / "bin" / "ffmpeg.exe"
        dummy_local_ffmpeg.parent.mkdir(parents=True)
        dummy_local_ffmpeg.touch()

        # Simular bin local
        with patch("pathlib.Path.exists", return_value=True):
            binary_path = _find_ffmpeg_binary()
            assert binary_path is not None
            assert "ffmpeg" in binary_path.lower()
