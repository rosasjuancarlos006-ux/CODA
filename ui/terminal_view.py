import datetime
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from core.events import DownloadPhase, ProgressEvent
from ui.view_interface import ViewInterface
from utils.file_manager import AudioFileInfo
from utils.format_validator import resolve_audio_format
from utils.platform_validator import (
    DEFAULT_PLATFORM,
    PLATFORM_DISPLAY_NAMES,
    PlatformType,
    normalize_platform_input,
)

logger = logging.getLogger(__name__)

# En Windows aseguramos que stdout maneje caracteres Unicode / utf-8 sin crashear en cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BANNER_ASCII = r"""
   ______ ____  ____   ___ 
  / ____// __ \/ __ \ /   |
 / /    / / / / / / // /| |
/ /___ / /_/ / /_/ // ___ |
\____/ \____/_____//_/  |_|
"""


class TerminalView:
    """
    Concrete implementation of ViewInterface using Rich for interactive terminal rendering.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console(highlight=False)
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None

    def show_banner(self) -> None:
        """Render the welcome banner."""
        banner_text = Text(BANNER_ASCII, style="bold cyan")
        tagline = Text("YouTube Music Downloader • High Quality Audio & ID3 Tags\n", style="dim white")
        self.console.print(banner_text)
        self.console.print(tagline)

    def show_main_menu(self) -> str:
        """Display the primary interactive options and return the user's choice."""
        menu_content = Text()
        menu_content.append("  [1] ", style="bold cyan")
        menu_content.append("Descargar música (Canción individual, Búsqueda o Playlist)\n", style="white")
        menu_content.append("  [2] ", style="bold cyan")
        menu_content.append("Ver biblioteca de descargas local\n", style="white")
        menu_content.append("  [3] ", style="bold red")
        menu_content.append("Salir de Coda", style="white")

        self.console.print(
            Panel(
                menu_content,
                title="[bold yellow]Panel de Control[/bold yellow]",
                subtitle="[dim]Selecciona una opción del 1 al 3[/dim]",
                border_style="bright_blue",
                padding=(1, 2)
            )
        )
        return self.console.input("[bold yellow]Selecciona una opción (1-3): [/bold yellow]").strip()

    def prompt_platform(self) -> str:
        """Prompt user for target platform ('youtube' or 'youtube_music')."""
        self.console.print("\n[bold cyan]Plataforma de Descarga[/bold cyan]")
        self.console.print("  [1] [white]YouTube (Catálogo general, videos, directos)[/white]")
        self.console.print("  [2] [white]YouTube Music (Pistas oficiales, álbumes, música de estudio)[/white]\n")

        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                raw_input = self.console.input("[cyan]Selecciona una plataforma [1/2] (Enter = YouTube): [/cyan]")
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
                self.show_warning("Opción no válida. Ingresa 1 (YouTube) o 2 (YouTube Music).")

        self.show_warning("Se superó el límite de reintentos. Se seleccionará YouTube por defecto.")
        logger.info("Max retries exceeded. Falling back to default platform: youtube")
        return DEFAULT_PLATFORM

    def prompt_query(self, platform_name: str) -> str:
        """Prompt user for search terms or resource URL."""
        self.console.print(f"\n[bold cyan]Descargar desde {platform_name}[/bold cyan]")
        return self.console.input("[white]Ingresa la URL (video/playlist) o término de búsqueda: [/white]").strip()

    def prompt_playlist_limit(self) -> Optional[int]:
        """Prompt user for download track limit for playlists (None = all)."""
        self.console.print("\n[bold yellow]Configuración de Playlist[/bold yellow]")
        limit_input = self.console.input("[cyan]¿Cuántas canciones deseas descargar? (Enter = todas): [/cyan]").strip()
        if not limit_input:
            return None

        try:
            parsed_limit = int(limit_input)
            if parsed_limit > 0:
                return parsed_limit
            else:
                self.show_warning("Ingresaste un valor menor o igual a 0. Se descargarán todas.")
                return None
        except ValueError:
            self.show_warning("Valor no numérico. Se descargarán todas por defecto.")
            return None

    def prompt_audio_format(self, is_playlist: bool) -> str:
        """Prompt user for desired audio format ('mp3', 'm4a', 'opus')."""
        if is_playlist:
            self.show_warning("El formato seleccionado aplicará a todas las canciones de la playlist.")

        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                raw_input = self.console.input("[cyan]Formato de audio [mp3/m4a/opus] (Enter = mp3): [/cyan]")
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
                self.show_warning("Opción no válida. Los formatos disponibles son: mp3, m4a, opus.")

        self.show_warning("Se superó el límite de reintentos. Se aplicará el formato por defecto: mp3.")
        logger.info("Max retries exceeded. Falling back to default format: mp3")
        return "mp3"

    def show_platform_mismatch(self, selected: str, adapted: str) -> None:
        """Display pedagogical notification of platform auto-adaptation."""
        sel_name = PLATFORM_DISPLAY_NAMES.get(selected, selected)
        det_name = PLATFORM_DISPLAY_NAMES.get(adapted, adapted)
        self.show_warning(f"Aviso: Habías seleccionado {sel_name}, pero el enlace pertenece a {det_name}.")
        self.show_info(f"Se adaptará automáticamente la descarga para procesar el contenido de {det_name}.")

    def show_info(self, message: str) -> None:
        """Display informational notification."""
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")

    def show_warning(self, message: str) -> None:
        """Display warning notification."""
        self.console.print(f"[bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")

    def show_error(self, message: str, error_type: Optional[str] = None) -> None:
        """Display error notification with optional error categorization."""
        raw_lower = message.lower()

        if error_type == "ffmpeg_missing" or "ffmpeg" in raw_lower:
            friendly_title = "Dependencia Faltante: FFmpeg"
            friendly_desc = (
                "No se encontró FFmpeg en el sistema ni en la carpeta 'bin/'.\n"
                "FFmpeg es indispensable para extraer y convertir el audio al formato deseado.\n"
                "Verifica que los archivos 'ffmpeg.exe' y 'ffprobe.exe' estén presentes en 'bin/' o en el PATH."
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
        elif any(term in raw_lower for term in ("getaddrinfo failed", "network is unreachable", "connection", "offline", "timeout")):
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

        self.console.print(
            Panel(
                Text(friendly_desc, style="white"),
                title=f"[bold red]✗ {friendly_title}[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
        )

    def show_single_success(self, result: Dict[str, Any]) -> None:
        """Display aesthetic completion summary for an individual track download."""
        title = result.get("title", "Desconocido")
        uploader = result.get("uploader", "Desconocido")
        duration = result.get("duration", 0)
        mins, secs = divmod(duration, 60)
        time_str = f"{mins}:{secs:02d} min" if duration else "N/A"
        path = result.get("mp3_path", "N/A")
        fmt = result.get("audio_format", "mp3").upper()

        meta_flag = result.get("metadata_applied")
        if meta_flag is True:
            meta_status = "✓ Incrustados (ID3v2 + Cover)"
        elif meta_flag == "partial":
            meta_status = "⚠ Parcial (Solo texto / Sin portada)"
        else:
            if fmt != "MP3":
                meta_status = f"⚠ No soportado para {fmt} (Audio intacto)"
            else:
                meta_status = "⚠ Falló al incrustar"

        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="bold cyan", justify="right")
        grid.add_column(style="white")

        grid.add_row("Título:", title)
        grid.add_row("Artista/Canal:", uploader)
        grid.add_row("Formato:", fmt)
        grid.add_row("Duración:", time_str)
        grid.add_row("Metadatos:", meta_status)
        grid.add_row("Guardado en:", str(path))

        self.console.print(
            Panel(
                grid,
                title="[bold green]✓ Descarga Completada con Éxito[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
        )

    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None:
        """Display table/panel summary for an entire playlist download."""
        playlist_title = summary.get("playlist_title", "Playlist")
        successful = summary.get("successful", [])
        failed = summary.get("failed", [])
        total_found = summary.get("total_in_playlist", 0)

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

        self.console.print(summary_table)

        stats_text = (
            f"[bold]Total en playlist:[/bold] {total_found}  |  "
            f"[bold green]Exitosas:[/bold green] {len(successful)}  |  "
            f"[bold red]Fallidas:[/bold red] {len(failed)}\n"
            f"[dim]Destino: {output_dir.resolve()}[/dim]"
        )
        self.console.print(Panel(stats_text, border_style="magenta", padding=(0, 1)))

    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None:
        """Render structured table displaying locally downloaded audio tracks."""
        table = Table(
            title="🎵 Biblioteca de Descargas",
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("Archivo", style="bold white")
        table.add_column("Formato", justify="center", style="bold green", width=10)
        table.add_column("Tamaño", justify="right", style="yellow", width=14)
        table.add_column("Fecha", justify="center", style="dim white", width=18)

        for item in downloads:
            size_mb = item.size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 0.1 else f"{item.size_bytes / 1024:.1f} KB"
            date_str = datetime.datetime.fromtimestamp(item.modified_timestamp).strftime("%Y-%m-%d %H:%M")
            table.add_row(item.name, item.format.upper(), size_str, date_str)

        self.console.print(table)

    def show_empty_downloads(self) -> None:
        """Display friendly notification when no downloaded tracks exist."""
        self.console.print(
            Panel(
                Text("No se encontraron archivos de audio descargados en la carpeta de salida.", style="dim italic"),
                title="Biblioteca Local",
                border_style="blue",
                padding=(1, 2)
            )
        )

    def start_progress_task(self, title: str, total: Optional[int] = None) -> None:
        """Initiate or activate a long-running progress visualization task."""
        self.stop_progress_task()
        self._progress = Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=30, style="dim white", complete_style="bold green"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        )
        self._progress.start()
        self._task_id = self._progress.add_task(title, total=total if total is not None else 100)

    def stop_progress_task(self) -> None:
        """Conclude and dismiss any active progress visualization."""
        if self._progress is not None:
            try:
                self._progress.stop()
            except Exception:
                pass
            self._progress = None
            self._task_id = None

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle incoming progress event and update presentation accordingly with graceful visual degradation."""
        desc = event.message
        if not desc:
            if event.phase == DownloadPhase.PREPARING:
                desc = "Consultando información del recurso..."
            elif event.phase == DownloadPhase.DOWNLOADING:
                desc = f"Descargando audio: {event.item_title or 'stream'}"
            elif event.phase == DownloadPhase.CONVERTING:
                desc = "Convirtiendo audio vía FFmpeg..."
            elif event.phase == DownloadPhase.METADATA:
                desc = "Inyectando metadatos y carátula..."
            elif event.phase == DownloadPhase.COMPLETED:
                desc = "Descarga completada."
            else:
                desc = "Procesando audio..."

        if event.current_item and event.total_items:
            prefix = f"[{event.current_item}/{event.total_items}] "
            desc = prefix + desc

        if self._progress is None or self._task_id is None:
            self.start_progress_task(desc, total=100)

        if self._progress is not None and self._task_id is not None:
            # Degradación visual: si percentage es None, mantiene barra indeterminada / spinner
            if event.percentage is not None:
                self._progress.update(self._task_id, description=desc, completed=event.percentage, total=100)
            else:
                self._progress.update(self._task_id, description=desc)
