import re

def sanitize_filename(filename: str) -> str:
    """Elimina o reemplaza caracteres no válidos en Windows para nombres de archivo."""
    # Caracteres no permitidos en Windows: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized.strip()
