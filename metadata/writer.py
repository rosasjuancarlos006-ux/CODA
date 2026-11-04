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
        logger.warning(f"No se pudo descargar portada ({response.status_code}): {thumbnail_url}")
    except requests.RequestException as e:
        logger.warning(f"Error de red descargando portada '{thumbnail_url}': {e}")
    except Exception as e:
        logger.error(f"Error inesperado descargando portada: {e}")
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


def write_id3_metadata(mp3_path: Path, metadata: dict) -> bool:
    """
    Escribe metadatos ID3v2 (Título, Artista, Álbum y Carátula) en el archivo MP3.
    """
    if not mp3_path.exists():
        logger.warning(f"No existe el archivo para inyectar tags: {mp3_path}")
        return False

    raw_title = metadata.get("title", "")
    raw_uploader = metadata.get("uploader", "")
    thumbnail_url = metadata.get("thumbnail")
    album_name = metadata.get("album", "YouTube Music")

    song_title, artist = clean_metadata_fields(raw_title, raw_uploader)

    # 1. Escribir tags de texto con EasyID3
    try:
        try:
            audio = EasyID3(str(mp3_path))
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(str(mp3_path))
            audio = EasyID3(str(mp3_path))

        audio["title"] = song_title
        audio["artist"] = artist
        audio["album"] = album_name
        audio.save()
        logger.debug(f"Tags EasyID3 guardados en {mp3_path.name}: title='{song_title}', artist='{artist}'")
    except Exception as e:
        logger.warning(f"No se pudieron escribir tags de texto en {mp3_path.name}: {e}")

    # 2. Incrustar imagen de portada con ID3 APIC
    if thumbnail_url:
        try:
            image_data = download_thumbnail(thumbnail_url)
            if image_data:
                tags = ID3(str(mp3_path))
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
                logger.debug(f"Carátula incrustada exitosamente en {mp3_path.name}")
        except Exception as e:
            logger.warning(f"No se pudo incrustar carátula en {mp3_path.name}: {e}")

    return True
