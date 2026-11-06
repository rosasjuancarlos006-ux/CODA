import logging
from typing import Optional
from utils.validator import classify_input, clean_video_url
from utils.platform_validator import PlatformType

logger = logging.getLogger(__name__)


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
