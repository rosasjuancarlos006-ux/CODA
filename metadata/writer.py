import logging
from pathlib import Path
from typing import Optional
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

logger = logging.getLogger(__name__)


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

    # 1. Escribir tags de texto con EasyID3 en MP3
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

    # 2. Incrustar imagen de portada con ID3 APIC en MP3
    if thumbnail_url:
        try:
            image_data = download_thumbnail(thumbnail_url)
            if image_data:
                tags = ID3(str(audio_path))
                mime_type = "image/jpeg" if ".jpg" in thumbnail_url or ".jpeg" in thumbnail_url else "image/png"
                tags.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime=mime_type,
                        type=3,  # Portada frontal (Front Cover)
                        desc="Cover",
                        data=image_data
                    )
                )
                tags.save(v2_version=3)
                logger.debug(f"Cover art successfully embedded in {audio_path.name}")
        except Exception as e:
            logger.warning(f"Failed to embed cover art in {audio_path.name}: {e}")

    return True
