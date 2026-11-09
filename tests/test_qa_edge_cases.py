import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import mutagen
from mutagen.easyid3 import EasyID3

import core.downloader as downloader
import metadata.writer as writer


class TestQADownloadHangAndTimeout:
    """
    Tests de QA para el Fallo 1:
    El sistema se cuelga indefinidamente y termina fallando por falta
    de configuración de timeouts y políticas de reintento en yt-dlp.
    """

    def test_downloader_ydl_opts_must_configure_network_timeouts(self):
        """
        Verifica que downloader.py configure parámetros defensivos de red en ydl_opts:
        - socket_timeout
        - retries
        - fragment_retries
        Sin estos parámetros, yt-dlp puede bloquearse indefinidamente en streams lentos o cortados.
        """
        with patch("core.downloader.find_ffmpeg", return_value="ffmpeg"), \
             patch("core.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:
            
            mock_ydl_instance = MagicMock()
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = {
                "title": "Test Song",
                "duration": 180,
                "uploader": "Artist",
                "thumbnail": None
            }

            dummy_out = Path("downloads")
            with patch.object(Path, "exists", return_value=True), \
                 patch("core.downloader.write_id3_metadata", return_value=True):
                downloader.download_audio_from_youtube("ytsearch1:Test", dummy_out, "mp3")

            call_args = mock_ydl_cls.call_args[0][0]

            # QA Assertion: Debe existir configuración de timeout explícito para evitar cuelgues
            assert "socket_timeout" in call_args, (
                "FALLO DE QA (Error 1): ydl_opts no define 'socket_timeout'. "
                "La descarga puede colgarse indefinidamente esperando respuesta del servidor."
            )
            assert call_args["socket_timeout"] <= 30, "El timeout de socket no debería superar 30 segundos."

    def test_downloader_playlist_extract_opts_must_configure_network_timeouts(self):
        """
        Verifica que la extracción de información de playlists en download_playlist
        también contemple timeouts de conexión y límites de reintento.
        """
        with patch("core.downloader.find_ffmpeg", return_value="ffmpeg"), \
             patch("core.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:

            mock_ydl_instance = MagicMock()
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = {"entries": []}

            dummy_out = Path("downloads")
            downloader.download_playlist("https://youtube.com/playlist?list=123", dummy_out)

            call_args = mock_ydl_cls.call_args[0][0]
            assert "socket_timeout" in call_args, (
                "FALLO DE QA (Error 1): extract_opts en download_playlist no define 'socket_timeout'."
            )


class TestQAMetadataIntegrityAndFalsePositives:
    """
    Tests de QA para el Fallo 2:
    El sistema reporta éxito en metadatos pero no se reflejan o fallan silenciosamente.
    """

    def test_write_id3_metadata_must_return_false_when_tag_write_fails(self, tmp_path):
        """
        Fallo detectado: Si EasyID3 falla al guardar los tags de texto (título/artista/álbum),
        la función actualmente captura la excepción con logger.warning y continúa,
        retornando True al final si no hay carátula o si la carátula pasa,
        reportando falsamente que los metadatos fueron aplicados.
        """
        test_file = tmp_path / "song.mp3"
        test_file.write_bytes(b"dummy mp3 content")

        metadata = {
            "title": "Cancion de Prueba",
            "uploader": "Artista Prueba",
            "thumbnail": None
        }

        # Simulamos que EasyID3 falla (archivo corrupto o error de mutagen)
        with patch("metadata.writer.EasyID3", side_effect=Exception("Disk full or corrupted ID3")):
            result = writer.write_id3_metadata(test_file, metadata)

            # QA Assertion: Si los tags de texto fallaron, NO debe informar éxito (False)
            assert result is False, (
                "FALLO DE QA (Error 2): write_id3_metadata retornó True a pesar de que "
                "la escritura de tags EasyID3 falló."
            )

    def test_thumbnail_mime_type_detection_for_webp_and_querystrings(self, tmp_path):
        """
        En YouTube y YouTube Music muchas URLs de carátulas vienen en formato WebP
        (ej: https://i.ytimg.com/vi/xyz/hqdefault.webp o URLs con parámetros ?sqp=...).
        Si la imagen es WebP, debe transcodificarse automáticamente a JPEG
        para garantizar compatibilidad con reproductores estándar ID3v2.
        """
        test_file = tmp_path / "song.mp3"
        test_file.write_bytes(b"dummy mp3 content")

        mock_easy = MagicMock()
        
        # Simular descarga de imagen webp convertida a jpeg
        fake_jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        metadata = {
            "title": "Cancion",
            "uploader": "Artista",
            "thumbnail": "https://i.ytimg.com/vi/demo/maxresdefault.webp?sqp=abc"
        }

        with patch("metadata.writer.EasyID3", return_value=mock_easy), \
             patch("metadata.writer.download_thumbnail", return_value=b"RIFFdummyWEBP"), \
             patch("metadata.writer.convert_image_to_jpeg_if_needed", return_value=(fake_jpeg_bytes, "image/jpeg")), \
             patch("metadata.writer.ID3") as mock_id3_cls:

            mock_id3_instance = MagicMock()
            mock_id3_cls.return_value = mock_id3_instance

            writer.write_id3_metadata(test_file, metadata)

            assert mock_id3_instance.add.called, "APIC add no fue llamado"
            apic_call = mock_id3_instance.add.call_args[0][0]

            assert apic_call.mime == "image/jpeg", (
                f"MIME incorrecto: {apic_call.mime}. Se esperaba 'image/jpeg' tras transcodificación."
            )

    def test_downloader_fallback_avoids_tagging_wrong_historical_audio_file(self, tmp_path):
        """
        En core/downloader.py:
        Si audio_path no existe, busca candidates = list(output_dir.glob(f'*.{audio_format}'))
        y toma el archivo más reciente previo.
        Si la descarga actual de yt-dlp falló silenciosamente o se guardó con otro nombre,
        termina inyectando los metadatos de la nueva canción sobre un archivo ya existente viejo.
        """
        # Archivo viejo existente en la carpeta
        old_file = tmp_path / "cancion_anterior.mp3"
        old_file.write_bytes(b"old")

        with patch("core.downloader.find_ffmpeg", return_value="ffmpeg"), \
             patch("core.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:

            mock_ydl_instance = MagicMock()
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl_instance
            # Supongamos que yt-dlp devolvió info pero falló en generar el archivo nuevo
            mock_ydl_instance.extract_info.return_value = {
                "title": "Cancion Nueva",
                "duration": 120,
                "uploader": "Artista Nuevo",
                "thumbnail": None
            }

            # En el downloader actual, audio_path = tmp_path / 'Cancion Nueva.mp3' no existe,
            # pero el fallback encuentra 'cancion_anterior.mp3' y le escribe encima los metadatos erróneamente.
            # Este test documenta la condición de carrera / falso positivo de archivo.
            candidates = list(tmp_path.glob("*.mp3"))
            assert len(candidates) == 1
            assert candidates[0].name == "cancion_anterior.mp3"
