import logging
from utils.validator import classify_input

logger = logging.getLogger(__name__)


def resolve_query(user_input: str) -> dict:
    """
    Analiza el texto de entrada y determina la query adecuada para yt-dlp.
    Si es un texto de búsqueda, antepone 'ytsearch1:' para obtener el resultado más relevante.
    """
    cleaned = (user_input or "").strip()
    input_type = classify_input(cleaned)

    if input_type == "search":
        # ytsearch1: le indica a yt-dlp que busque en YouTube y descargue el 1er resultado
        query = f"ytsearch1:{cleaned}"
    else:
        query = cleaned

    logger.debug(f"Input resuelto: modo={input_type}, query='{query}'")

    return {
        "mode": input_type,
        "query": query,
        "original_input": cleaned
    }
