import logging
from pathlib import Path
import shutil
import time
from typing import Callable, Optional, Union
import yt_dlp

from core.events import DownloadPhase, ProgressEvent
from metadata.writer import write_id3_metadata

logger = logging.getLogger(__name__)

# Ruta local donde colocamos los binarios estáticos
FFMPEG_DIR = Path(__file__).resolve().parent.parent / "bin"


def find_ffmpeg() -> str | None:
    """
    Busca ffmpeg en el siguiente orden:
    1. Carpeta local bin/ del proyecto
    2. PATH global del sistema
    Retorna la ruta al binario, o None si no existe.
    """
    local_ffmpeg = FFMPEG_DIR / "ffmpeg.exe"
    if local_ffmpeg.exists():
        logger.debug(f"FFmpeg encontrado localmente en: {local_ffmpeg}")
        return str(local_ffmpeg)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.debug(f"FFmpeg detectado en el PATH del sistema: {system_ffmpeg}")
        return system_ffmpeg

    logger.warning("No se encontró FFmpeg ni en bin/ ni en el PATH del sistema.")
    return None


def download_audio_from_youtube(
    query: str,
    output_dir: Path,
    audio_format: str = "mp3",
    on_progress: Optional[Callable[[ProgressEvent], None]] = None
) -> dict:
    """
    Descarga el audio de un video o búsqueda de YouTube y lo convierte al formato deseado (mp3, m4a, opus) con metadatos.
    Emite eventos de progreso desacoplados (ProgressEvent) si se proporciona el callback 'on_progress'.
    """
    logger.info(f"Iniciando descarga individual con query: '{query}' en formato: '{audio_format}'")

    if on_progress:
        on_progress(
            ProgressEvent(
                phase=DownloadPhase.PREPARING,
                message=f"Consultando información para: {query}"
            )
        )

    # 1. Validar que FFmpeg exista ANTES de intentar descargar
    ffmpeg_binary = find_ffmpeg()
    if not ffmpeg_binary:
        err_msg = (
            "FFmpeg no fue detectado en la carpeta 'bin/' ni en el PATH del sistema.\n"
            "      Es indispensable para convertir los streams de YouTube al formato seleccionado."
        )
        logger.error("FFmpeg no encontrado. Abortando descarga.")
        if on_progress:
            on_progress(ProgressEvent(phase=DownloadPhase.ERROR, message=err_msg))
        return {
            "success": False,
            "error": "ffmpeg_missing",
            "message": err_msg
        }

    outtmpl = str(output_dir / "%(title)s.%(ext)s")
    download_start_time = time.time()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'noplaylist': True,  # Forzar descarga individual en esta función
        'ffmpeg_location': ffmpeg_binary,
        'socket_timeout': 15,
        'retries': 3,
        'fragment_retries': 3,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    if on_progress:
        def ydl_hook(d: dict):
            status = d.get('status')
            if status == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                percentage = (downloaded_bytes / total_bytes * 100.0) if total_bytes else None
                speed = d.get('speed')
                eta = d.get('eta')
                filename = d.get('filename', '')
                title = Path(filename).stem if filename else None
                on_progress(
                    ProgressEvent(
                        phase=DownloadPhase.DOWNLOADING,
                        percentage=percentage,
                        speed_bytes_sec=speed,
                        eta_seconds=eta,
                        item_title=title,
                        message="Descargando flujo de audio..."
                    )
                )
            elif status == 'finished':
                on_progress(
                    ProgressEvent(
                        phase=DownloadPhase.CONVERTING,
                        percentage=100.0,
                        message=f"Convirtiendo audio a {audio_format.upper()} vía FFmpeg..."
                    )
                )
        ydl_opts['progress_hooks'] = [ydl_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(query, download=True)

            if not info_dict:
                logger.error(f"yt-dlp no devolvió información para query: '{query}'")
                if on_progress:
                    on_progress(ProgressEvent(phase=DownloadPhase.ERROR, message="No se pudo obtener información del video."))
                return {
                    "success": False,
                    "error": "no_info",
                    "message": "No se pudo obtener información del video."
                }

            # En caso de búsqueda ytsearch, info_dict contiene una lista 'entries'
            if "entries" in info_dict and info_dict["entries"]:
                video_info = info_dict["entries"][0]
            else:
                video_info = info_dict

            title = video_info.get('title', 'Desconocido')
            duration = video_info.get('duration', 0)
            uploader = video_info.get('uploader', 'Desconocido')
            thumbnail = video_info.get('thumbnail')

            # Ubicar el archivo de audio resultante para incrustar metadatos
            audio_path = output_dir / f"{title}.{audio_format}"

            # Si el nombre exacto no concuerda, buscar únicamente archivos generados durante esta descarga
            if not audio_path.exists():
                candidates = [
                    f for f in output_dir.glob(f"*.{audio_format}")
                    if f.stat().st_mtime >= (download_start_time - 1.0)
                ]
                if candidates:
                    audio_path = max(candidates, key=lambda f: f.stat().st_mtime)

            metadata_applied = False
            if audio_path.exists():
                if on_progress:
                    on_progress(
                        ProgressEvent(
                            phase=DownloadPhase.METADATA,
                            item_title=title,
                            message="Incrustando etiquetas y carátula..."
                        )
                    )
                meta_payload = {
                    "title": title,
                    "uploader": uploader,
                    "thumbnail": thumbnail
                }
                metadata_applied = write_id3_metadata(audio_path, meta_payload)
            else:
                logger.warning(f"No se encontró el archivo {audio_format.upper()} resultante en {output_dir}")

            logger.info(f"Descarga exitosa: '{title}' por '{uploader}' -> {audio_path.name}")
            if on_progress:
                on_progress(
                    ProgressEvent(
                        phase=DownloadPhase.COMPLETED,
                        percentage=100.0,
                        item_title=title,
                        message="Descarga completada con éxito."
                    )
                )

            return {
                "success": True,
                "title": title,
                "duration": duration,
                "uploader": uploader,
                "mp3_path": str(audio_path),
                "audio_format": audio_format,
                "metadata_applied": metadata_applied
            }
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Error de descarga yt-dlp con query '{query}': {e}")
        if on_progress:
            on_progress(ProgressEvent(phase=DownloadPhase.ERROR, message=str(e)))
        return {
            "success": False,
            "error": "download_failed",
            "message": str(e)
        }
    except Exception as e:
        logger.exception(f"Excepción inesperada al procesar '{query}': {e}")
        if on_progress:
            on_progress(ProgressEvent(phase=DownloadPhase.ERROR, message=str(e)))
        return {
            "success": False,
            "error": "unknown",
            "message": str(e)
        }


def download_playlist(
    playlist_url: str,
    output_dir: Path,
    limit: int = 0,
    on_progress: Optional[Callable[..., None]] = None,
    audio_format: str = "mp3"
) -> dict:
    """
    Descarga todos los videos de una playlist de YouTube como audio con metadatos en el formato especificado.
    Soporta callbacks con ProgressEvent y callbacks legacy (current, total, title, status).
    """
    logger.info(f"Iniciando descarga de playlist: '{playlist_url}' en formato '{audio_format}' con límite: {limit}")

    def notify(event: ProgressEvent, legacy_status: str = "downloading"):
        if not on_progress:
            return
        try:
            on_progress(event)
        except TypeError:
            # Fallback para callbacks de 4 argumentos: (current, total, title, status)
            on_progress(
                event.current_item or 0,
                event.total_items or 0,
                event.item_title or "",
                legacy_status
            )

    ffmpeg_binary = find_ffmpeg()
    if not ffmpeg_binary:
        logger.error("FFmpeg no encontrado para descarga de playlist.")
        notify(
            ProgressEvent(
                phase=DownloadPhase.ERROR,
                message="FFmpeg no fue detectado en la carpeta 'bin/' ni en el PATH del sistema."
            ),
            legacy_status="error"
        )
        return {
            "success": False,
            "error": "ffmpeg_missing",
            "message": "FFmpeg no fue detectado en la carpeta 'bin/' ni en el PATH del sistema."
        }

    extract_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'ffmpeg_location': ffmpeg_binary,
        'socket_timeout': 15,
        'retries': 3,
        'fragment_retries': 3,
    }

    try:
        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
    except Exception as e:
        logger.error(f"Fallo al extraer metadatos de la playlist '{playlist_url}': {e}")
        notify(ProgressEvent(phase=DownloadPhase.ERROR, message=str(e)), legacy_status="error")
        return {
            "success": False,
            "error": "playlist_extract_failed",
            "message": str(e)
        }

    if not playlist_info:
        logger.error("No se pudo obtener información de la playlist.")
        notify(ProgressEvent(phase=DownloadPhase.ERROR, message="No se pudo obtener información de la playlist."), legacy_status="error")
        return {
            "success": False,
            "error": "playlist_extract_failed",
            "message": "No se pudo obtener información de la playlist."
        }

    entries = list(playlist_info.get("entries", []))
    if not entries:
        logger.warning(f"La playlist '{playlist_url}' está vacía o sin videos accesibles.")
        return {
            "success": False,
            "error": "empty_playlist",
            "message": "La playlist está vacía o no tiene videos accesibles."
        }

    playlist_title = playlist_info.get("title", "Playlist de YouTube")
    total_found = len(entries)
    logger.info(f"Playlist '{playlist_title}' cargada con {total_found} pistas detectadas.")

    if limit > 0:
        entries = entries[:limit]

    total_to_download = len(entries)
    successful = []
    failed = []

    for i, entry in enumerate(entries, start=1):
        if not entry:
            continue

        video_url = entry.get("url") or entry.get("id")
        video_title = entry.get("title", f"Pista {i}")

        if not video_url:
            err_text = "URL/ID del video no disponible"
            logger.warning(f"Pista #{i} '{video_title}' sin URL válida.")
            failed.append({
                "index": i,
                "title": video_title,
                "error": err_text
            })
            notify(
                ProgressEvent(
                    phase=DownloadPhase.ERROR,
                    current_item=i,
                    total_items=total_to_download,
                    item_title=video_title,
                    message=err_text
                ),
                legacy_status="error"
            )
            continue

        if not str(video_url).startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"

        notify(
            ProgressEvent(
                phase=DownloadPhase.DOWNLOADING,
                current_item=i,
                total_items=total_to_download,
                item_title=video_title,
                message=f"Descargando pista {i}/{total_to_download}: {video_title}"
            ),
            legacy_status="downloading"
        )

        def item_progress_forwarder(evt: ProgressEvent):
            notify(
                ProgressEvent(
                    phase=evt.phase,
                    percentage=evt.percentage,
                    speed_bytes_sec=evt.speed_bytes_sec,
                    eta_seconds=evt.eta_seconds,
                    current_item=i,
                    total_items=total_to_download,
                    item_title=video_title,
                    message=evt.message
                ),
                legacy_status="downloading"
            )

        result = download_audio_from_youtube(
            video_url,
            output_dir,
            audio_format=audio_format,
            on_progress=item_progress_forwarder
        )

        if result.get("success"):
            successful.append({
                "index": i,
                "title": result.get("title"),
                "uploader": result.get("uploader"),
                "mp3_path": result.get("mp3_path")
            })
            notify(
                ProgressEvent(
                    phase=DownloadPhase.COMPLETED,
                    current_item=i,
                    total_items=total_to_download,
                    item_title=result.get("title"),
                    message=f"Pista {i}/{total_to_download} completada."
                ),
                legacy_status="done"
            )
        else:
            err_desc = result.get("message", "Error desconocido")
            logger.warning(f"Fallo al descargar pista #{i} '{video_title}': {err_desc}")
            failed.append({
                "index": i,
                "title": video_title,
                "error": err_desc
            })
            notify(
                ProgressEvent(
                    phase=DownloadPhase.ERROR,
                    current_item=i,
                    total_items=total_to_download,
                    item_title=video_title,
                    message=err_desc
                ),
                legacy_status="error"
            )

    logger.info(f"Resumen playlist '{playlist_title}': {len(successful)} exitosas, {len(failed)} fallidas.")
    return {
        "success": True,
        "playlist_title": playlist_title,
        "total_in_playlist": total_found,
        "total_attempted": total_to_download,
        "successful": successful,
        "failed": failed
    }
