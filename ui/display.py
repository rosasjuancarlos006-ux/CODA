import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, MofNCompleteColumn

from utils.format_validator import resolve_audio_format
from utils.platform_validator import (
    PlatformType,
    PLATFORM_DISPLAY_NAMES,
    DEFAULT_PLATFORM,
    normalize_platform_input
)

logger = logging.getLogger(__name__)

# En Windows aseguramos que stdout maneje caracteres Unicode / utf-8 sin crashear en cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False)

BANNER_ASCII = r"""
   ______ ____  ____   ___ 
  / ____// __ \/ __ \ /   |
 / /    / / / / / / // /| |
/ /___ / /_/ / /_/ // ___ |
\____/ \____/_____//_/  |_|
"""


def show_banner():
    """Muestra el banner ASCII de bienvenida con estilo moderno y degradado sutil."""
    banner_text = Text(BANNER_ASCII, style="bold cyan")
    tagline = Text("YouTube Music Downloader • High Quality Audio & ID3 Tags\n", style="dim white")
    console.print(banner_text)
    console.print(tagline)


def show_menu():
    """Renderiza el menú principal en un panel estilizado."""
    menu_content = Text()
    menu_content.append("  [1] ", style="bold cyan")
    menu_content.append("Descargar música (Canción individual, Búsqueda o Playlist)\n", style="white")
    menu_content.append("  [2] ", style="bold cyan")
    menu_content.append("Ver biblioteca de descargas local\n", style="white")
    menu_content.append("  [3] ", style="bold red")
    menu_content.append("Salir de Coda", style="white")

    console.print(
        Panel(
            menu_content,
            title="[bold yellow]Panel de Control[/bold yellow]",
            subtitle="[dim]Selecciona una opción del 1 al 3[/dim]",
            border_style="bright_blue",
            padding=(1, 2)
        )
    )


def show_info(msg: str):
    """Muestra un mensaje informativo estilizado."""
    console.print(f"[bold blue]ℹ[/bold blue] {msg}")


def show_warning(msg: str):
    """Muestra una advertencia."""
    console.print(f"[bold yellow]⚠[/bold yellow] [yellow]{msg}[/yellow]")


def get_platform_display_name(platform: str) -> str:
    """Retorna el nombre para mostrar de una plataforma o la cadena original."""
    return PLATFORM_DISPLAY_NAMES.get(platform, platform)


def show_platform_mismatch_warning(selected: str, detected: str):
    """Muestra una advertencia y mensaje pedagógico ante discrepancia de plataforma."""
    sel_name = get_platform_display_name(selected)
    det_name = get_platform_display_name(detected)
    show_warning(f"Aviso: Habías seleccionado {sel_name}, pero el enlace pertenece a {det_name}.")
    show_info(f"Se adaptará automáticamente la descarga para procesar el contenido de {det_name}.")


def prompt_platform() -> PlatformType:
    """
    Solicita interactivamente la plataforma al usuario (YouTube o YouTube Music)
    con hasta 3 reintentos. Retorna 'youtube' o 'youtube_music'.
    Si se agotan los reintentos, selecciona 'youtube' por defecto.
    """
    console.print("[bold cyan]Plataforma de Descarga[/bold cyan]")
    console.print("  [1] [white]YouTube (Catálogo general, videos, directos)[/white]")
    console.print("  [2] [white]YouTube Music (Pistas oficiales, álbumes, música de estudio)[/white]\n")

    retries = 0
    max_retries = 3

    while retries < max_retries:
        try:
            raw_input = console.input("[cyan]Selecciona una plataforma [1/2] (Enter = YouTube): [/cyan]")
        except KeyboardInterrupt:
            logger.info("Platform selection interrupted by user.")
            raise

        is_valid, chosen_platform = normalize_platform_input(raw_input)

        if is_valid and chosen_platform is not None:
            logger.info(f"Selected platform: {chosen_platform}")
            return chosen_platform

        retries += 1
        logger.debug(f"Invalid platform option entered: '{raw_input}'")

        if retries < max_retries:
            show_warning("Opción no válida. Ingresa 1 (YouTube) o 2 (YouTube Music).")

    show_warning("Se superó el límite de reintentos. Se seleccionará YouTube por defecto.")
    logger.info("Max retries exceeded. Falling back to default platform: youtube")
    return DEFAULT_PLATFORM


def prompt_audio_format(is_playlist: bool = False) -> str:
    """
    Solicita interactivamente el formato de audio al usuario con hasta 3 reintentos.
    Retorna 'mp3', 'm4a' u 'opus'. Si se supera el límite de intentos, selecciona 'mp3'.
    """
    if is_playlist:
        show_warning("El formato seleccionado aplicará a todas las canciones de la playlist.")

    retries = 0
    max_retries = 3

    while retries < max_retries:
        try:
            raw_input = console.input("[cyan]Formato de audio [mp3/m4a/opus] (Enter = mp3): [/cyan]")
        except KeyboardInterrupt:
            logger.info("Format selection interrupted by user.")
            raise

        is_valid, chosen_format = resolve_audio_format(raw_input)

        if is_valid:
            logger.info(f"Selected audio format: {chosen_format}")
            return chosen_format

        retries += 1
        logger.debug(f"Invalid format option entered: '{raw_input}'")

        if retries < max_retries:
            show_warning("Opción no válida. Los formatos disponibles son: mp3, m4a, opus.")

    show_warning("Se superó el límite de reintentos. Se aplicará el formato por defecto: mp3.")
    logger.info("Max retries exceeded. Falling back to default format: mp3")
    return "mp3"


def show_success_single(song_data: Dict[str, Any]):
    """Muestra un panel detallado y limpio con la información del track descargado."""
    title = song_data.get("title", "Desconocido")
    uploader = song_data.get("uploader", "Desconocido")
    duration = song_data.get("duration", 0)
    mins, secs = divmod(duration, 60)
    time_str = f"{mins}:{secs:02d} min" if duration else "N/A"
    path = song_data.get("mp3_path", "N/A")
    fmt = song_data.get("audio_format", "mp3").upper()

    if song_data.get("metadata_applied"):
        meta_status = "✓ Incrustados (ID3v2 + Cover)"
    else:
        if fmt != "MP3":
            meta_status = f"⚠ No soportado para {fmt} (Audio intacto)"
        else:
            meta_status = "⚠ Pendiente / Error al incrustar"

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", justify="right")
    grid.add_column(style="white")

    grid.add_row("Título:", title)
    grid.add_row("Artista/Canal:", uploader)
    grid.add_row("Formato:", fmt)
    grid.add_row("Duración:", time_str)
    grid.add_row("Metadatos:", meta_status)
    grid.add_row("Guardado en:", str(path))

    console.print(
        Panel(
            grid,
            title="[bold green]✓ Descarga Completada con Éxito[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
    )


def show_playlist_summary(result: Dict[str, Any], output_dir: Path):
    """Muestra una tabla con el resumen de la playlist descargada."""
    playlist_title = result.get("playlist_title", "Playlist")
    successful = result.get("successful", [])
    failed = result.get("failed", [])
    total_found = result.get("total_in_playlist", 0)

    summary_table = Table(
        title=f"Resumen de Playlist: {playlist_title}",
        title_style="bold magenta",
        header_style="bold cyan",
        border_style="bright_blue"
    )
    summary_table.add_column("#", justify="center", style="dim", width=4)
    summary_table.add_column("Pista / Título", style="white")
    summary_table.add_column("Estado", justify="center", width=12)

    for item in successful:
        summary_table.add_row(
            str(item.get("index", "-")),
            item.get("title", "Sin título"),
            "[bold green]Completado[/bold green]"
        )

    for item in failed:
        summary_table.add_row(
            str(item.get("index", "-")),
            item.get("title", "Sin título"),
            "[bold red]Falló[/bold red]"
        )

    console.print(summary_table)

    stats_text = (
        f"[bold]Total en playlist:[/bold] {total_found}  |  "
        f"[bold green]Exitosas:[/bold green] {len(successful)}  |  "
        f"[bold red]Fallidas:[/bold red] {len(failed)}\n"
        f"[dim]Destino: {output_dir.resolve()}[/dim]"
    )
    console.print(Panel(stats_text, border_style="magenta", padding=(0, 1)))


def show_error(message: str, error_type: Optional[str] = None):
    """
    Categoriza y muestra errores amigables para el usuario final
    (video privado, sin conexión, falta de ffmpeg, etc.).
    """
    raw_lower = message.lower()

    if error_type == "ffmpeg_missing" or "ffmpeg" in raw_lower:
        friendly_title = "Dependencia Faltante: FFmpeg"
        friendly_desc = (
            "No se encontró FFmpeg en el sistema ni en la carpeta 'bin/'.\n"
            "FFmpeg es indispensable para extraer y convertir el audio al formato deseado.\n"
            "Verifica que los archivos 'ffmpeg.exe' y 'ffprobe.exe' estén presentes en 'bin/'."
        )
    elif "private video" in raw_lower or "este video es privado" in raw_lower:
        friendly_title = "Video Privado o No Disponible"
        friendly_desc = (
            "El video solicitado tiene restricciones de privacidad o ha sido eliminado por el autor."
        )
    elif "sign in to confirm your age" in raw_lower or "age-restricted" in raw_lower:
        friendly_title = "Restricción de Edad"
        friendly_desc = (
            "Este video requiere inicio de sesión en YouTube por restricción de edad y no puede descargarse anónimamente."
        )
    elif "getaddrinfo failed" in raw_lower or "network is unreachable" in raw_lower or "connection" in raw_lower or "offline" in raw_lower:
        friendly_title = "Error de Conexión a Internet"
        friendly_desc = (
            "No fue posible conectar con los servidores de YouTube.\n"
            "Por favor verifica tu conexión a internet e inténtalo de nuevo."
        )
    elif "is not a valid url" in raw_lower:
        friendly_title = "Enlace Inválido"
        friendly_desc = "El enlace proporcionado no coincide con una URL válida de YouTube."
    else:
        friendly_title = "Error en la Operación"
        friendly_desc = message if len(message) < 200 else f"{message[:200]}..."

    console.print(
        Panel(
            Text(friendly_desc, style="white"),
            title=f"[bold red]✗ {friendly_title}[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
    )


def show_downloads_table(downloads_dir: Path):
    """Muestra la lista de archivos descargados localmente con tamaño y formato en una tabla estética."""
    if not downloads_dir.exists():
        show_warning(f"La carpeta '{downloads_dir}' no existe aún.")
        return

    # Soportar archivos de audio MP3, M4A, OPUS y otros
    audio_extensions = {".mp3", ".m4a", ".opus"}
    audio_files = [f for f in downloads_dir.glob("*") if f.suffix.lower() in audio_extensions and f.is_file()]
    other_files = [f for f in downloads_dir.glob("*") if f.suffix.lower() not in audio_extensions and f.is_file()]

    if not audio_files and not other_files:
        console.print(
            Panel(
                Text("La carpeta de descargas está vacía.", style="dim italic"),
                title="Biblioteca Local",
                border_style="blue"
            )
        )
        return

    table = Table(
        title=f"Biblioteca de Descargas ({downloads_dir.resolve()})",
        header_style="bold cyan",
        border_style="blue"
    )
    table.add_column("Archivo", style="white")
    table.add_column("Formato", justify="center", style="bold green", width=10)
    table.add_column("Tamaño (MB)", justify="right", style="cyan", width=14)

    for f in audio_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        fmt_label = f.suffix.replace(".", "").upper()
        table.add_row(f.name, fmt_label, f"{size_mb:.2f} MB")

    for f in other_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        table.add_row(f.name, f.suffix.replace(".", "").upper() or "FILE", f"{size_mb:.2f} MB")

    console.print(table)


def create_playlist_progress() -> Progress:
    """Crea un objeto Progress configurado con barra de progreso estilizada para playlists."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=35, style="dim white", complete_style="bold green"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    )
