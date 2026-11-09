import io
import logging
from pathlib import Path
import shutil
import subprocess
from typing import Optional, Tuple
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

logger = logging.getLogger(__name__)

# Intentar soporte opcional de Pillow para transcodificar WebP a JPEG
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def _find_ffmpeg_binary() -> Optional[str]:
    """Busca FFmpeg en bin/ local o PATH sin generar import circular."""
    local_bin = Path(__file__).resolve().parent.parent / "bin" / "ffmpeg.exe"
    if local_bin.exists():
        return str(local_bin)
    return shutil.which("ffmpeg")


def convert_image_to_jpeg_if_needed(image_bytes: bytes, mime_type: str) -> Tuple[bytes, str]:
    """
    Convierte imágenes (especialmente WebP) a JPEG para máxima compatibilidad
    con reproductores multimedia ID3v2. Utiliza Pillow si está disponible o
    el binario local de FFmpeg como motor de transcodificación.
    """
    if not image_bytes:
        return image_bytes, mime_type

    # Si ya es JPEG o PNG estándar no requiere conversión
    if mime_type in ["image/jpeg", "image/jpg"]:
        return image_bytes, mime_type

    # 1. Intentar con Pillow si está instalado
    if HAS_PILLOW:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            logger.debug("Thumbnail converted to JPEG via Pillow for ID3 compatibility")
            return buffer.getvalue(), "image/jpeg"
        except Exception as e:
            logger.warning(f"Could not convert thumbnail to JPEG via Pillow: {e}")

    # 2. Transcodificar mediante FFmpeg del proyecto (sin requerir dependencias pip extras)
    ffmpeg_bin = _find_ffmpeg_binary()
    if ffmpeg_bin:
        try:
            proc = subprocess.run(
                [
                    ffmpeg_bin,
                    "-loglevel", "error",
                    "-i", "pipe:0",
                    "-f", "image2pipe",
                    "-vcodec", "mjpeg",
                    "-q:v", "2",
                    "pipe:1"
                ],
                input=image_bytes,
                capture_output=True,
                timeout=10
            )
            if proc.returncode == 0 and proc.stdout:
                logger.debug("Thumbnail converted to JPEG via FFmpeg for ID3 compatibility")
                return proc.stdout, "image/jpeg"
            else:
                logger.warning(f"FFmpeg image transcode failed: {proc.stderr.decode(errors='replace')}")
        except Exception as e:
            logger.warning(f"FFmpeg image conversion error: {e}")

    return image_bytes, mime_type


def detect_image_mime(thumbnail_url: str, image_bytes: Optional[bytes] = None) -> str:
    """Detecta el tipo MIME de la imagen por magic numbers o extensión de URL."""
    if image_bytes:
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
            return "image/webp"

    url_lower = thumbnail_url.lower()
    if ".jpg" in url_lower or ".jpeg" in url_lower:
        return "image/jpeg"
    if ".png" in url_lower:
        return "image/png"
    if ".webp" in url_lower:
        return "image/webp"

    return "image/jpeg"


def download_thumbnail(thumbnail_url: str) -> Optional[bytes]:
    """Descarga los bytes de la imagen de portada desde una URL con timeout seguro."""
    if not thumbnail_url:
        return None
    try:
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code == 200:
            return response.content
        logger.warning(f"Could not download thumbnail (status {response.status_code}): {thumbnail_url}")
    except requests.RequestException as e:
        logger.warning(f"Network error downloading thumbnail '{thumbnail_url}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading thumbnail: {e}")
    return None


def clean_metadata_fields(title: str, uploader: str) -> tuple[str, str]:
    """
    Intenta separar Artista y Título si el título del video tiene el formato:
    'Artista - Canción' o 'Artista - Canción (Official Video)'.
    """
    artist = (uploader or "Desconocido").strip()
    song_title = (title or "Desconocido").strip()

    if " - " in title:
        parts = title.split(" - ", 1)
        artist = parts[0].strip() or artist
        song_title = parts[1].strip() or song_title

    return song_title, artist


def write_id3_metadata(audio_path: Path, metadata: dict) -> bool:
    """
    Escribe metadatos y carátula con degradación elegante según el formato de audio.
    - Para MP3: Inyecta etiquetas EasyID3 y carátula APIC.
      Retorna True si al menos los tags de texto se guardaron exitosamente.
      Si los tags de texto fallan, retorna False.
    - Para otros formatos (M4A, OPUS): Conserva el archivo de audio intacto y emite
      log en inglés informando si la inyección no está soportada o no pudo aplicarse.
    """
    if not audio_path.exists():
        logger.warning(f"Target audio file does not exist: {audio_path}")
        return False

    suffix = audio_path.suffix.lower()

    # Si no es archivo MP3, degradar elegantemente sin corromper el audio
    if suffix != ".mp3":
        logger.warning(
            f"Metadata and cover art embedding is currently restricted to MP3. "
            f"Audio file '{audio_path.name}' preserved intact without ID3 tags."
        )
        return False

    raw_title = metadata.get("title", "")
    raw_uploader = metadata.get("uploader", "")
    thumbnail_url = metadata.get("thumbnail")
    album_name = metadata.get("album", "YouTube Music")

    song_title, artist = clean_metadata_fields(raw_title, raw_uploader)

    # 1. Escribir tags de texto con EasyID3 en MP3 (requisito mandatorio)
    try:
        try:
            audio = EasyID3(str(audio_path))
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(str(audio_path))
            audio = EasyID3(str(audio_path))

        audio["title"] = song_title
        audio["artist"] = artist
        audio["album"] = album_name
        audio.save()
        logger.debug(f"EasyID3 tags saved in {audio_path.name}: title='{song_title}', artist='{artist}'")
    except Exception as e:
        logger.warning(f"Failed to write text tags to {audio_path.name}: {e}")
        return False

    # 2. Incrustar imagen de portada con ID3 APIC en MP3 (opcional/secundario)
    if thumbnail_url:
        try:
            image_data = download_thumbnail(thumbnail_url)
            if image_data:
                detected_mime = detect_image_mime(thumbnail_url, image_data)
                final_data, final_mime = convert_image_to_jpeg_if_needed(image_data, detected_mime)

                tags = ID3(str(audio_path))
                tags.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime=final_mime,
                        type=3,  # Portada frontal (Front Cover)
                        desc="Cover",
                        data=final_data
                    )
                )
                tags.save(v2_version=3)
                logger.debug(f"Cover art successfully embedded in {audio_path.name}")
        except Exception as e:
            logger.warning(f"Failed to embed cover art in {audio_path.name}: {e}")

    return True
