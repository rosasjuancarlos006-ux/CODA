import argparse
from typing import Optional


def parse_arguments() -> argparse.Namespace:
    """
    Parsea argumentos CLI opcionales para Coda.
    Si se invoca sin argumentos, la aplicación continuará normalmente al flujo guiado/interactivo.
    """
    parser = argparse.ArgumentParser(
        prog="coda",
        description="Coda - Descargador de música y playlists desde YouTube a MP3 (192 kbps)",
        epilog="Ejecuta 'python main.py' sin parámetros para iniciar la aplicación interactiva."
    )

    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="URL directa de YouTube o texto de búsqueda de la canción/playlist a descargar."
    )

    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=None,
        help="Límite máximo de canciones a procesar en caso de descargar una playlist (0 = todas)."
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Directorio de destino personalizado para las descargas."
    )

    return parser.parse_args()
