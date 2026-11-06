import re
from typing import Optional, Tuple, Literal, Dict

PlatformType = Literal["youtube", "youtube_music"]

SUPPORTED_PLATFORMS: Tuple[PlatformType, ...] = ("youtube", "youtube_music")
DEFAULT_PLATFORM: PlatformType = "youtube"

PLATFORM_DISPLAY_NAMES: Dict[PlatformType, str] = {
    "youtube": "YouTube",
    "youtube_music": "YouTube Music"
}

_YOUTUBE_ALIASES = {"1", "youtube", "yt"}
_YOUTUBE_MUSIC_ALIASES = {"2", "youtube music", "music", "ytmusic", "yt_music"}


def normalize_platform_input(raw_input: Optional[str]) -> Tuple[bool, Optional[PlatformType]]:
    """
    Limpia los espacios en blanco a los extremos, colapsa espacios internos múltiples a uno solo
    y convierte la cadena a minúsculas. Valida contra los alias aceptados de YouTube y YouTube Music.

    Retorna:
        Tuple[bool, Optional[PlatformType]]:
            - (True, "youtube") si es vacío o coincide con alias de YouTube.
            - (True, "youtube_music") si coincide con alias de YouTube Music.
            - (False, None) si no es válido.
    """
    if raw_input is None or not isinstance(raw_input, str):
        return True, DEFAULT_PLATFORM

    cleaned = raw_input.strip()
    if not cleaned:
        return True, DEFAULT_PLATFORM

    # Colapsar múltiples espacios internos a uno solo y pasar a minúsculas
    collapsed = re.sub(r'\s+', ' ', cleaned).lower()

    if collapsed in _YOUTUBE_ALIASES:
        return True, "youtube"

    if collapsed in _YOUTUBE_MUSIC_ALIASES:
        return True, "youtube_music"

    return False, None


def detect_url_platform(url: Optional[str]) -> Optional[PlatformType]:
    """
    Analiza el dominio de una URL y retorna a qué plataforma pertenece:
    - 'youtube_music' si contiene music.youtube.com
    - 'youtube' si contiene youtube.com o youtu.be (y no es music.youtube.com)
    - None si no coincide o no es una URL reconocida.
    """
    if not url or not isinstance(url, str):
        return None

    cleaned = url.strip()

    # Regex para YouTube Music
    if re.search(r'^(https?://)?(www\.)?music\.youtube\.com(/.*)?$', cleaned, re.IGNORECASE):
        return "youtube_music"

    # Regex para YouTube estándar (youtube.com o youtu.be)
    if re.search(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)(/.*)?$', cleaned, re.IGNORECASE):
        return "youtube"

    return None


def check_platform_mismatch(selected_platform: PlatformType, url: str) -> Tuple[bool, PlatformType]:
    """
    Función pura que determina si hay discrepancia entre la plataforma elegida y el enlace suministrado.

    Retorna:
        Tuple[bool, PlatformType]:
            - (True, detected_platform) si la URL pertenece a la otra plataforma (requiere auto-adaptación).
            - (False, selected_platform) si coinciden o si la entrada es texto libre.
    """
    detected = detect_url_platform(url)

    if detected is not None and detected != selected_platform:
        return True, detected

    return False, selected_platform
