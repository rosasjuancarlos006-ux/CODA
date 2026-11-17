from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import yt_dlp

from core.events import DownloadPhase, ProgressEvent
from core.downloader import download_audio_from_youtube, download_playlist
from core.resolver import buscar_top_coincidencias, resolve_query


# =====================================================================
# QA Test Suite: Resolver y Downloader Mockeado (Tarea 1.3)
# =====================================================================


class TestResolverCoreQA:
    """Pruebas exhaustivas para resolve_query y buscar_top_coincidencias con mocks de red."""

    def test_tc_1_3_1_resolve_query_all_modes_and_platforms(self):
        """Verifica la resolución de queries contextual según modo y plataforma."""
        # 1. Búsqueda en YouTube estándar
        res_yt = resolve_query("Bad Bunny Tití me preguntó", platform="youtube")
        assert res_yt["mode"] == "search"
        assert res_yt["query"] == "ytsearch1:Bad Bunny Tití me preguntó"

        # 2. Búsqueda en YouTube Music (agrega Audio Oficial)
        res_ytm = resolve_query("Rosalía Despechá", platform="youtube_music")
        assert res_ytm["mode"] == "search"
        assert res_ytm["query"] == "ytsearch1:Rosalía Despechá Audio Oficial"

        # 3. Video individual limpio
        res_vid = resolve_query("https://www.youtube.com/watch?v=dQw4w9WgXcQ", platform="youtube")
        assert res_vid["mode"] == "video"
        assert res_vid["query"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # 4. Video con parámetros de mix (debe quedar podado a video puro)
        res_mix = resolve_query(
            "https://music.youtube.com/watch?v=abc123xyz&list=RDAMVMabc123xyz",
            platform="youtube_music",
        )
        assert res_mix["mode"] == "video"
        assert res_mix["query"] == "https://music.youtube.com/watch?v=abc123xyz"

        # 5. Playlist pura (no se poda)
        pl_url = "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
        res_pl = resolve_query(pl_url, platform="youtube")
        assert res_pl["mode"] == "playlist"
        assert res_pl["query"] == pl_url

        # 6. Entradas vacías o None caen a search vacío
        res_empty = resolve_query("", platform="youtube")
        assert res_empty["mode"] == "search"
        assert res_empty["query"] == "ytsearch1:"

    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_1_buscar_top_coincidencias_mocked(self, mock_ydl_cls):
        """buscar_top_coincidencias formatea homogéneamente los 5 mejores resultados."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        mock_instance.extract_info.return_value = {
            "entries": [
                {
                    "id": "vid1",
                    "title": "Cancion 1",
                    "uploader": "Artista 1",
                    "channel": "Canal 1",
                    "duration": 215,
                    "url": "https://www.youtube.com/watch?v=vid1",
                },
                {
                    "id": "vid2",
                    "title": "Cancion 2",
                    "uploader": "Artista 2",
                    "channel": "Canal 2",
                    "duration": None,  # Duración desconocida
                    "url": None,
                },
            ]
        }

        results = buscar_top_coincidencias("Dua Lipa", limite=2, platform="youtube_music")
        assert len(results) == 2
        assert results[0]["id"] == "vid1"
        assert results[0]["duration_str"] == "03:35"
        assert results[0]["version"] == "Audio oficial"

        assert results[1]["id"] == "vid2"
        assert results[1]["duration_str"] == "--:--"
        assert results[1]["url"] == "https://www.youtube.com/watch?v=vid2"


class TestDownloaderCoreQA:
    """Pruebas exhaustivas para download_audio_from_youtube y download_playlist con mocks de yt-dlp."""

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("core.downloader.write_id3_metadata", return_value=True)
    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_2_download_audio_success_lifecycle(
        self,
        mock_ydl_cls,
        mock_meta,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """Ciclo de vida completo exitoso emitiendo eventos de progreso y generando metadatos."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        # Crear archivo resultante simulado en tmp_path
        (tmp_path / "Prueba Track.mp3").touch()

        def fake_extract_info(query, download=True):
            # Disparar simulación de hook de progreso si está configurado
            hooks = mock_ydl_cls.call_args[0][0].get("progress_hooks", [])
            for h in hooks:
                h({"status": "downloading", "downloaded_bytes": 500, "total_bytes": 1000, "speed": 1024, "eta": 1, "filename": "Prueba Track.part"})
                h({"status": "finished"})
            return {
                "title": "Prueba Track",
                "duration": 180,
                "uploader": "Artista Prueba",
                "thumbnail": "https://img.youtube.com/vi/123/0.jpg",
            }

        mock_instance.extract_info.side_effect = fake_extract_info

        captured_events: list[ProgressEvent] = []

        result = download_audio_from_youtube(
            query="https://www.youtube.com/watch?v=123",
            output_dir=tmp_path,
            audio_format="mp3",
            on_progress=captured_events.append,
        )

        assert result["success"] is True
        assert result["title"] == "Prueba Track"
        assert result["metadata_applied"] is True

        phases = [e.phase for e in captured_events]
        assert DownloadPhase.PREPARING in phases
        assert DownloadPhase.DOWNLOADING in phases
        assert DownloadPhase.CONVERTING in phases
        assert DownloadPhase.METADATA in phases
        assert DownloadPhase.COMPLETED in phases

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_3_download_audio_network_error_handled(
        self,
        mock_ydl_cls,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """Manejo de DownloadError de yt-dlp retornando dict con success=False sin lanzar excepción."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Video no disponible en su país")

        captured_events: list[ProgressEvent] = []

        res = download_audio_from_youtube(
            query="https://www.youtube.com/watch?v=bloqueado",
            output_dir=tmp_path,
            on_progress=captured_events.append,
        )

        assert res["success"] is False
        assert res["error"] == "download_failed"
        assert "Video no disponible" in res["message"]
        assert any(e.phase == DownloadPhase.ERROR for e in captured_events)

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_3_download_audio_empty_info_handled(
        self,
        mock_ydl_cls,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """Manejo de retorno None de extract_info sin propagar excepción."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = None

        res = download_audio_from_youtube(
            query="https://www.youtube.com/watch?v=invalido",
            output_dir=tmp_path,
        )
        assert res["success"] is False
        assert res["error"] == "no_info"

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("core.downloader.download_audio_from_youtube")
    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_4_download_playlist_with_limit_and_summary(
        self,
        mock_ydl_cls,
        mock_download_single,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """download_playlist respeta el parámetro limit y resume exitosas y fallidas."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        mock_instance.extract_info.return_value = {
            "title": "Mi Playlist Favorita",
            "entries": [
                {"id": "v1", "url": "https://www.youtube.com/watch?v=v1", "title": "Pista 1"},
                {"id": "v2", "url": "https://www.youtube.com/watch?v=v2", "title": "Pista 2"},
                {"id": "v3", "url": "https://www.youtube.com/watch?v=v3", "title": "Pista 3"},
            ],
        }

        # Simular descarga: v1 exitosa, v2 fallida
        mock_download_single.side_effect = [
            {"success": True, "title": "Pista 1", "uploader": "Artista 1", "mp3_path": "Pista 1.mp3"},
            {"success": False, "error": "timeout", "message": "Tiempo de espera agotado"},
        ]

        captured_events: list[ProgressEvent] = []

        summary = download_playlist(
            playlist_url="https://www.youtube.com/playlist?list=PL123",
            output_dir=tmp_path,
            limit=2,  # Debe procesar únicamente 2 de los 3
            on_progress=captured_events.append,
            audio_format="mp3",
        )

        assert summary["success"] is True
        assert summary["total_attempted"] == 2
        assert len(summary["successful"]) == 1
        assert len(summary["failed"]) == 1
        assert summary["successful"][0]["title"] == "Pista 1"
        assert summary["failed"][0]["title"] == "Pista 2"

    @patch("core.downloader.find_ffmpeg", return_value="ffmpeg")
    @patch("yt_dlp.YoutubeDL")
    def test_tc_1_3_4_download_playlist_empty_handled(
        self,
        mock_ydl_cls,
        mock_ffmpeg,
        tmp_path: Path,
    ):
        """download_playlist maneja listas vacías retornando empty_playlist."""
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.extract_info.return_value = {"title": "Lista Vacía", "entries": []}

        res = download_playlist(
            playlist_url="https://www.youtube.com/playlist?list=PLvacia",
            output_dir=tmp_path,
        )
        assert res["success"] is False
        assert res["error"] == "empty_playlist"
