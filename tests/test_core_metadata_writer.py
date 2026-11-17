from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from metadata.writer import (
    clean_metadata_fields,
    convert_image_to_jpeg_if_needed,
    detect_image_mime,
    download_thumbnail,
    write_id3_metadata,
)


# =====================================================================
# QA Test Suite: Metadatos ID3 y Degradación Elegante (Tarea 1.4)
# =====================================================================


class TestMetadataWriterCoreQA:
    """Pruebas exhaustivas para la inyección de metadatos ID3 y degradación elegante."""

    def test_tc_1_4_1_clean_metadata_fields_separation(self):
        """Verifica la separación de artista y título a partir del título del video."""
        # Formato 'Artista - Canción'
        title, artist = clean_metadata_fields(
            "Coldplay - Viva La Vida",
            uploader="Coldplay Official",
        )
        assert title == "Viva La Vida"
        assert artist == "Coldplay"

        # Formato con sufijos adicionales
        title2, artist2 = clean_metadata_fields(
            "Dua Lipa - Houdini (Official Video)",
            uploader="Dua Lipa",
        )
        assert title2 == "Houdini (Official Video)"
        assert artist2 == "Dua Lipa"

        # Título sin delimitador ' - ' usa el uploader como fallback de artista
        title3, artist3 = clean_metadata_fields(
            "Bohemian Rhapsody",
            uploader="Queen",
        )
        assert title3 == "Bohemian Rhapsody"
        assert artist3 == "Queen"

        # Entradas vacías
        title_empty, artist_empty = clean_metadata_fields("", "")
        assert title_empty == "Desconocido"
        assert artist_empty == "Desconocido"

    def test_tc_1_4_1_detect_image_mime_by_magic_numbers_and_url(self):
        """Detección precisa del tipo MIME por cabecera binaria o extensión."""
        # Magic numbers JPEG: \xff\xd8\xff
        assert detect_image_mime("https://img.com/pic", b"\xff\xd8\xff\xe0\x00\x10JFIF") == "image/jpeg"

        # Magic numbers PNG: \x89PNG\r\n\x1a\n
        assert detect_image_mime("https://img.com/pic", b"\x89PNG\r\n\x1a\n\x00\x00") == "image/png"

        # Magic numbers WebP: RIFF....WEBP
        assert detect_image_mime("https://img.com/pic", b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"

        # Fallback por URL cuando no hay bytes
        assert detect_image_mime("https://img.com/cover.webp?size=small") == "image/webp"
        assert detect_image_mime("https://img.com/cover.png") == "image/png"
        assert detect_image_mime("https://img.com/cover.jpg") == "image/jpeg"
        assert detect_image_mime("https://img.com/unknown_ext") == "image/jpeg"

    @patch("metadata.writer.requests.get")
    def test_tc_1_4_2_download_thumbnail_resilience(self, mock_requests_get):
        """Descarga de miniaturas HTTP con timeouts y manejo de errores 404/500."""
        # 1. Éxito 200
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake-image-bytes"
        mock_requests_get.return_value = mock_resp

        data = download_thumbnail("https://example.com/thumb.jpg")
        assert data == b"fake-image-bytes"

        # 2. Error HTTP 404
        mock_resp_404 = MagicMock()
        mock_resp_404.status_code = 404
        mock_requests_get.return_value = mock_resp_404
        assert download_thumbnail("https://example.com/404.jpg") is None

        # 3. Timeout o excepción de red
        import requests
        mock_requests_get.side_effect = requests.exceptions.ConnectTimeout("Timeout")
        assert download_thumbnail("https://example.com/timeout.jpg") is None

        # 4. URL vacía o None
        assert download_thumbnail("") is None

    @patch("metadata.writer.download_thumbnail", return_value=b"\xff\xd8\xff\xe0\x00\x10JFIFfake")
    def test_tc_1_4_2_write_id3_metadata_mp3_success(self, mock_download_thumb, tmp_path: Path):
        """Inyección exitosa de EasyID3 y APIC en archivo MP3 sintético."""
        mp3_file = tmp_path / "cancion.mp3"
        # Cabecera básica de archivo MP3
        mp3_file.write_bytes(b"\xff\xfb\x90\x04" + b"\x00" * 2048)

        metadata = {
            "title": "Beso - Rosalía",
            "uploader": "Rosalía",
            "thumbnail": "https://img.youtube.com/thumb.jpg",
            "album": "RR",
        }

        success = write_id3_metadata(mp3_file, metadata)
        assert success is True
        assert mp3_file.exists()

        # Verificar lectura de tags
        from mutagen.easyid3 import EasyID3
        tags = EasyID3(str(mp3_file))
        assert "Beso" in tags["title"][0] or "Rosalía" in tags["title"][0]
        assert "album" in tags

    def test_tc_1_4_3_write_id3_metadata_graceful_degradation_non_mp3(self, tmp_path: Path):
        """Degradación elegante: M4A y OPUS se preservan intactos sin inyectar ID3v2."""
        m4a_file = tmp_path / "cancion.m4a"
        m4a_file.write_bytes(b"AAC-STREAM-DATA")

        opus_file = tmp_path / "cancion.opus"
        opus_file.write_bytes(b"OPUS-STREAM-DATA")

        meta = {"title": "Test Track", "uploader": "Artist"}

        # Para M4A no se inyecta ID3v2 y retorna False, pero el archivo permanece intacto
        res_m4a = write_id3_metadata(m4a_file, meta)
        assert res_m4a is False
        assert m4a_file.read_bytes() == b"AAC-STREAM-DATA"

        # Para OPUS no se inyecta ID3v2 y retorna False, pero el archivo permanece intacto
        res_opus = write_id3_metadata(opus_file, meta)
        assert res_opus is False
        assert opus_file.read_bytes() == b"OPUS-STREAM-DATA"

    def test_tc_1_4_3_write_id3_metadata_nonexistent_file(self, tmp_path: Path):
        """Retorna False de forma segura si el archivo de audio no existe en disco."""
        ghost_path = tmp_path / "no_existe.mp3"
        assert write_id3_metadata(ghost_path, {"title": "Test"}) is False
