import logging
from typing import Any, Dict, List, Optional
import yt_dlp

from utils.validator import classify_input, clean_video_url
from utils.platform_validator import PlatformType

logger = logging.getLogger(__name__)


def buscar_top_coincidencias(termino: str, limite: int = 5, platform: PlatformType = "youtube") -> List[Dict[str, Any]]:
    """
    Busca los N mejores resultados en YouTube usando yt-dlp de manera ligera (extract_flat).
    Retorna una lista de diccionarios con formato homogéneo para la UI.
    """
    cleaned = (termino or "").strip()
    if not cleaned:
        return []

    search_query = f"{cleaned} Audio Oficial" if platform == "youtube_music" else cleaned
    query = f"ytsearch{limite}:{search_query}"

    ydl_opts = {
        "extract_flat": True,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if not info:
                return []

            entries = info.get("entries") or []
            results: List[Dict[str, Any]] = []

            for entry in entries[:limite]:
                if not entry:
                    continue

                duration = entry.get("duration")
                if duration and isinstance(duration, (int, float)):
                    mins = int(duration) // 60
                    secs = int(duration) % 60
                    duration_str = f"{mins:02d}:{secs:02d}"
                else:
                    duration_str = "--:--"

                video_id = entry.get("id") or ""
                url = entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
                if not url.startswith("http"):
                    url = f"https://www.youtube.com/watch?v={video_id}"

                results.append({
                    "id": video_id,
                    "title": entry.get("title") or "Pista desconocida",
                    "artist": entry.get("uploader") or entry.get("channel") or "Artista desconocido",
                    "channel": entry.get("channel") or entry.get("uploader") or "Canal",
                    "version": "Audio oficial" if platform == "youtube_music" else "Estándar",
                    "duration_str": duration_str,
                    "duration": duration,
                    "url": url,
                })

            return results
    except Exception as e:
        logger.error(f"Error al buscar coincidencias para '{termino}': {e}")
        raise


def resolve_query(user_input: Optional[str], platform: PlatformType = "youtube") -> dict:
    """
    Analiza el texto de entrada y determina la query adecuada para yt-dlp según la plataforma.
    - Si es una URL de video individual, poda parámetros de listas/mixes (&list=RD...).
    - Si es un texto de búsqueda:
      - En 'youtube': antepone 'ytsearch1:{query}'.
      - En 'youtube_music': antepone 'ytsearch1:{query} Audio Oficial' para priorizar pistas de estudio.
    """
    cleaned = (user_input or "").strip()
    input_type = classify_input(cleaned)

    if input_type == "search":
        if platform == "youtube_music":
            search_term = f"{cleaned} Audio Oficial".strip()
            query = f"ytsearch1:{search_term}"
        else:
            query = f"ytsearch1:{cleaned}"
    elif input_type == "video":
        query = clean_video_url(cleaned)
    else:
        query = cleaned

    logger.debug(f"Input resuelto: plataforma={platform}, modo={input_type}, query='{query}'")

    return {
        "mode": input_type,
        "query": query,
        "original_input": cleaned
    }
