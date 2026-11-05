from typing import Optional, Tuple

SUPPORTED_FORMATS: Tuple[str, ...] = ("mp3", "m4a", "opus")
DEFAULT_FORMAT: str = "mp3"


def normalize_format_input(raw_input: Optional[str]) -> str:
    """
    Limpia los espacios en blanco a los extremos y convierte la cadena a minúsculas.
    Si el valor recibido es None o no es cadena, retorna una cadena vacía.
    """
    if not raw_input or not isinstance(raw_input, str):
        return ""
    return raw_input.strip().lower()


def is_valid_format(formatted_text: str) -> bool:
    """
    Verifica si el texto normalizado corresponde a uno de los formatos soportados.
    Rechaza cadenas con longitud superior a 20 caracteres para evitar entradas anómalas.
    """
    if not formatted_text or len(formatted_text) > 20:
        return False
    return formatted_text in SUPPORTED_FORMATS


def resolve_audio_format(raw_input: Optional[str]) -> Tuple[bool, str]:
    """
    Determina si la entrada es válida y cuál es el formato final resultante.

    Retorna:
        Tuple[bool, str]:
            - (True, "mp3") si la entrada está vacía o son solo espacios (por defecto).
            - (True, format_str) si coincide con un formato soportado ('mp3', 'm4a', 'opus').
            - (False, "") si la opción no es válida.
    """
    normalized = normalize_format_input(raw_input)

    # Selección por defecto cuando se envía vacío o solo espacios
    if not normalized:
        return True, DEFAULT_FORMAT

    if is_valid_format(normalized):
        return True, normalized

    return False, ""
