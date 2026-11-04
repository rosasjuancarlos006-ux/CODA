import re
from typing import Literal

InputType = Literal["video", "playlist", "search"]

YOUTUBE_URL_PATTERNS = [
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
]

PLAYLIST_PATTERNS = [
    r'^(https?://)?(www\.)?youtube\.com/playlist\?list=.+$',
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+[&?]list=[^&]+'
]

def is_valid_youtube_url(text: str) -> bool:
    """Valida si el texto ingresado tiene estructura de URL de YouTube."""
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    return any(re.match(pattern, text) for pattern in YOUTUBE_URL_PATTERNS)

def is_playlist_url(text: str) -> bool:
    """Detecta si la URL corresponde a una lista de reproduccion."""
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    return any(re.match(pattern, text) for pattern in PLAYLIST_PATTERNS)

def classify_input(text: str) -> InputType:
    """
    Clasifica la entrada del usuario en:
    - 'playlist': si es una URL de playlist
    - 'video': si es una URL directa de video
    - 'search': si es un texto para buscar en YouTube
    """
    if not text or not isinstance(text, str):
        return "search"

    text = text.strip()
    if is_playlist_url(text):
        return "playlist"
    if is_valid_youtube_url(text):
        return "video"
    return "search"
