import re
from typing import Literal, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

InputType = Literal["video", "playlist", "search"]

# Patrones para URLs válidas de YouTube y YouTube Music
YOUTUBE_URL_PATTERNS = [
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+$'
]

# Patrones para URLs de playlists puras
PLAYLIST_PATTERNS = [
    r'^(https?://)?(www\.)?(youtube\.com|music\.youtube\.com)/playlist\?list=.+$',
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+[&?]list=[^&]+'
]


def clean_video_url(url: Optional[str]) -> str:
    """
    Poda parámetros innecesarios de una URL de video (&list=..., &index=..., &feature=...),
    dejando únicamente la URL base del video con su identificador 'v'.
    Si no es una URL de video o es inválida, retorna la cadena original o vacía.
    """
    if not url or not isinstance(url, str):
        return ""

    url_str = url.strip()

    # Si es URL de playlist pura (/playlist?list=...), no se debe alterar
    if "/playlist" in url_str:
        return url_str

    try:
        parsed = urlparse(url_str)
        # Manejo de URLs con esquema relativo o sin esquema (ej: www.youtube.com/watch?v=...)
        if not parsed.netloc and "/" in url_str:
            # Reintentar parseando con https:// temporal
            dummy_parsed = urlparse(f"https://{url_str}")
            if "watch" in dummy_parsed.path and "v" in parse_qs(dummy_parsed.query):
                qs = parse_qs(dummy_parsed.query)
                video_id = qs.get("v", [""])[0]
                if video_id:
                    new_query = urlencode({"v": video_id})
                    return urlunparse(("", "", dummy_parsed.path, "", new_query, "")).lstrip("/")

        if "watch" in parsed.path:
            qs = parse_qs(parsed.query)
            video_id = qs.get("v", [""])[0]
            if video_id:
                new_query = urlencode({"v": video_id})
                return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", new_query, ""))
    except Exception:
        pass

    return url_str


def is_valid_youtube_url(text: str) -> bool:
    """Valida si el texto ingresado tiene estructura de URL de YouTube o YouTube Music."""
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    return any(re.match(pattern, text) for pattern in YOUTUBE_URL_PATTERNS)


def is_playlist_url(text: str) -> bool:
    """
    Detecta si la URL corresponde a una lista de reproducción pura.
    Si la URL contiene '/watch' con un parámetro de video ('v='), se prioriza
    como video individual para evitar descargar listas infinitas o radios mix.
    """
    if not text or not isinstance(text, str):
        return False
    text = text.strip()

    # Si es un video individual con mix (ej. watch?v=...&list=RD...), se prioriza como video
    if "watch" in text and ("?v=" in text or "&v=" in text):
        return False

    return any(re.match(pattern, text) for pattern in PLAYLIST_PATTERNS)


def classify_input(text: str) -> InputType:
    """
    Clasifica la entrada del usuario en:
    - 'playlist': si es una URL de playlist pura
    - 'video': si es una URL directa de video (incluso con mix / radio adjunto)
    - 'search': si es un texto para buscar en el catálogo
    """
    if not text or not isinstance(text, str):
        return "search"

    text = text.strip()
    if is_playlist_url(text):
        return "playlist"
    if is_valid_youtube_url(text):
        return "video"
    return "search"
