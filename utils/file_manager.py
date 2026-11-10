import logging
import os
from pathlib import Path
import re
from dataclasses import dataclass
from typing import List, Set

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {".mp3", ".m4a", ".opus"}
PARTIAL_EXTENSIONS: Set[str] = {".part", ".ytdl", ".temp", ".tmp"}


@dataclass(frozen=True)
class AudioFileInfo:
    """Represents a downloaded audio file and its metadata."""
    name: str
    path: Path
    format: str
    size_bytes: int
    modified_timestamp: float


def sanitize_filename(filename: str) -> str:
    """Elimina o reemplaza caracteres no válidos en Windows para nombres de archivo."""
    # Caracteres no permitidos en Windows: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized.strip()


def scan_audio_downloads(directory: Path) -> List[AudioFileInfo]:
    """
    Escanea un directorio y retorna metadatos de los archivos de audio soportados (.mp3, .m4a, .opus).
    Retorna la lista ordenada descendentemente por fecha de modificación (más reciente primero).
    """
    if not directory.exists() or not directory.is_dir():
        return []

    audio_files: List[AudioFileInfo] = []
    try:
        for entry in directory.iterdir():
            if entry.is_file() and entry.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                try:
                    stat_info = entry.stat()
                    audio_files.append(
                        AudioFileInfo(
                            name=entry.name,
                            path=entry.resolve(),
                            format=entry.suffix.lower().lstrip("."),
                            size_bytes=stat_info.st_size,
                            modified_timestamp=stat_info.st_mtime,
                        )
                    )
                except OSError as e:
                    logger.warning(f"No se pudo leer la información de {entry}: {e}")
    except OSError as e:
        logger.error(f"Error accediendo al directorio {directory}: {e}")
        return []

    # Ordenar por fecha de modificación descendente
    audio_files.sort(key=lambda x: x.modified_timestamp, reverse=True)
    return audio_files


def find_partial_download_files(output_dir: Path, download_start_timestamp: float) -> List[Path]:
    """
    Identifica archivos temporales o incompletos generados a partir de una marca de tiempo dada.
    Detecta extensiones temporales (.part, .ytdl, .temp, .tmp) o archivos de audio modificados
    durante la descarga en curso.
    """
    if not output_dir.exists() or not output_dir.is_dir():
        return []

    partial_files: List[Path] = []
    try:
        for entry in output_dir.iterdir():
            if not entry.is_file():
                continue

            lower_name = entry.name.lower()
            is_temp_ext = any(lower_name.endswith(ext) for ext in PARTIAL_EXTENSIONS)
            is_audio_ext = entry.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

            if is_temp_ext or is_audio_ext:
                try:
                    if entry.stat().st_mtime >= download_start_timestamp:
                        partial_files.append(entry.resolve())
                except OSError:
                    continue
    except OSError as e:
        logger.error(f"Error buscando archivos parciales en {output_dir}: {e}")

    return partial_files


def cleanup_files(file_paths: List[Path]) -> int:
    """
    Elimina de forma segura la lista de rutas recibidas, capturando excepciones
    de sistema de archivos sin propagar fallos. Retorna la cantidad de archivos eliminados.
    """
    deleted_count = 0
    for path in file_paths:
        try:
            if path.exists() and path.is_file():
                path.unlink(missing_ok=True)
                deleted_count += 1
                logger.debug(f"Archivo eliminado: {path}")
        except OSError as e:
            logger.warning(f"No se pudo eliminar el archivo {path}: {e}")

    return deleted_count
