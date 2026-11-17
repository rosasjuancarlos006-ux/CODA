import io
from pathlib import Path
import subprocess
import threading
import time
from unittest.mock import MagicMock, patch
import pytest

from core.downloader import download_audio_from_youtube
from core.events import DownloadPhase, ProgressEvent


# =====================================================================
# QA Test Suite: Subprocesos en Daemon Thread / No-TTY (Tarea 2.3)
# =====================================================================


class TestSubprocessDaemonPipesQA:
    """
    Pruebas de compatibilidad para ejecución de yt-dlp y FFmpeg dentro de hilos
    secundarios daemon sin consola interactiva (TTY redirigido / capturado).
    """

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("core.downloader.write_id3_metadata", return_value=True)
    @patch("yt_dlp.YoutubeDL")
    def test_tc_2_3_1_downloader_in_daemon_thread_without_tty(
        self,
        mock_ydl_cls,
        mock_meta,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """
        Verifica que download_audio_from_youtube se ejecute sin bloqueos ni
        errores de codificación de salida cuando se despacha dentro de un hilo daemon
        con sys.stdout redirigido (emulando el entorno GUI de Flet).
        """
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        (tmp_path / "Daemon Pista.mp3").touch()
        mock_instance.extract_info.return_value = {
            "title": "Daemon Pista",
            "duration": 200,
            "uploader": "Artista Daemon",
            "thumbnail": None,
        }

        thread_result: dict = {}
        captured_events: list[ProgressEvent] = []
        thread_exception: list[Exception] = []

        def worker_target():
            try:
                # Simular captura/redirección de buffer sin terminal interactiva
                with patch("sys.stdout", new=io.StringIO()), patch("sys.stderr", new=io.StringIO()):
                    res = download_audio_from_youtube(
                        query="https://www.youtube.com/watch?v=daemon123",
                        output_dir=tmp_path,
                        audio_format="mp3",
                        on_progress=captured_events.append,
                    )
                    thread_result.update(res)
            except Exception as exc:
                thread_exception.append(exc)

        daemon_thread = threading.Thread(target=worker_target, daemon=True, name="TestDaemonWorker")
        daemon_thread.start()
        daemon_thread.join(timeout=5.0)

        assert not daemon_thread.is_alive(), "El hilo daemon sufrió un deadlock o no terminó a tiempo."
        assert len(thread_exception) == 0, f"Excepción en hilo daemon: {thread_exception}"
        assert thread_result.get("success") is True
        assert thread_result.get("title") == "Daemon Pista"

    def test_tc_2_3_2_ffmpeg_subprocess_pipe_nonblocking(self, tmp_path: Path):
        """
        Verifica que una llamada a FFmpeg con buffers de pipe redirigidos
        (capture_output=True) no provoque un deadlock si se satura el buffer de salida.
        """
        from core.downloader import find_ffmpeg
        ffmpeg_bin = find_ffmpeg()
        if not ffmpeg_bin or not Path(ffmpeg_bin).exists():
            pytest.skip("FFmpeg no disponible para prueba de pipe no bloqueante.")

        # Generar un comando FFmpeg que escriba información a stderr sin bloquear el pipe
        cmd = [
            ffmpeg_bin,
            "-f", "lavfi",
            "-i", "sine=frequency=1000:duration=0.5",
            "-f", "null",
            "-",
        ]

        def run_proc(res_holder: dict):
            proc = subprocess.run(cmd, capture_output=True, timeout=5)
            res_holder["returncode"] = proc.returncode
            res_holder["has_stderr"] = len(proc.stderr) > 0

        res_data: dict = {}
        t = threading.Thread(target=run_proc, args=(res_data,), daemon=True)
        t.start()
        t.join(timeout=5.0)

        assert not t.is_alive(), "FFmpeg subprocess call blocked in background thread."
        assert res_data.get("returncode") == 0
        assert res_data.get("has_stderr") is True
