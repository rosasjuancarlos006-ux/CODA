import logging
import sys
from pathlib import Path

from config import DOWNLOADS_DIR, DEFAULT_PLAYLIST_LIMIT
from core.resolver import resolve_query
from core.downloader import download_audio_from_youtube, download_playlist
from ui.cli import parse_arguments
from ui import display

logger = logging.getLogger("coda.main")


def handle_playlist_download(playlist_url: str, output_dir: Path, requested_limit: int | None = None):
    """Flujo de interacción y renderizado con Rich para descarga de playlists."""
    limit = DEFAULT_PLAYLIST_LIMIT

    if requested_limit is not None:
        limit = requested_limit if requested_limit > 0 else DEFAULT_PLAYLIST_LIMIT
    else:
        display.console.print("\n[bold yellow]Configuración de Playlist[/bold yellow]")
        limit_input = display.console.input("[cyan]¿Cuántas canciones deseas descargar? (Enter = todas): [/cyan]").strip()
        if limit_input:
            try:
                parsed_limit = int(limit_input)
                if parsed_limit > 0:
                    limit = parsed_limit
                else:
                    display.show_warning("Ingresaste un valor menor o igual a 0. Se descargarán todas.")
            except ValueError:
                display.show_warning("Valor no numérico. Se descargarán todas por defecto.")

    # Solicitar formato de audio para toda la playlist
    audio_format = display.prompt_audio_format(is_playlist=True)

    try:
        with display.console.status("[bold cyan]Consultando información de la playlist en YouTube...", spinner="dots"):
            progress = display.create_playlist_progress()
            task_id = None

            def progress_callback(current: int, total: int, title: str, status: str):
                nonlocal task_id
                if task_id is None:
                    task_id = progress.add_task("[cyan]Descargando playlist...", total=total)
                progress.update(task_id, completed=current, description=f"[cyan]{title[:30]}...")

            with progress:
                result = download_playlist(
                    playlist_url=playlist_url,
                    output_dir=output_dir,
                    limit=limit,
                    on_progress=progress_callback,
                    audio_format=audio_format
                )

        if not result.get("success"):
            display.show_error(result.get("message", "Error procesando playlist"), error_type=result.get("error"))
            return

        display.show_playlist_summary(result, output_dir)
    except KeyboardInterrupt:
        logger.info("Descarga de playlist interrumpida por el usuario.")
        display.show_warning("Descarga cancelada por el usuario.")
    except Exception as e:
        logger.exception(f"Error imprevisto en handle_playlist_download: {e}")
        display.show_error(f"Error inesperado al procesar la playlist: {e}")


def handle_single_download(query: str, output_dir: Path, audio_format: str | None = None):
    """Flujo para descargar y mostrar feedback estético de una canción individual."""
    if audio_format is None:
        audio_format = display.prompt_audio_format(is_playlist=False)

    try:
        with display.console.status(
            f"[bold cyan]Descargando audio, convirtiendo a {audio_format.upper()} e inyectando metadatos...",
            spinner="dots"
        ):
            result = download_audio_from_youtube(query, output_dir, audio_format=audio_format)

        if result.get("success"):
            display.show_success_single(result)
        else:
            display.show_error(result.get("message", "Error al descargar"), error_type=result.get("error"))
    except KeyboardInterrupt:
        logger.info("Descarga individual cancelada por el usuario.")
        display.show_warning("Descarga cancelada por el usuario.")
    except Exception as e:
        logger.exception(f"Error imprevisto en handle_single_download: {e}")
        display.show_error(f"Error inesperado durante la descarga: {e}")


def handle_download_prompt(output_dir: Path):
    """Solicita la entrada al usuario en el modo interactivo."""
    display.console.print("\n[bold cyan]Descargar Audio o Playlist[/bold cyan]")
    user_input = display.console.input("[white]Ingresa la URL (video/playlist) o término de búsqueda: [/white]").strip()

    if not user_input:
        display.show_warning("No ingresaste ningún texto o enlace.")
        return

    resolved = resolve_query(user_input)
    mode = resolved["mode"]
    query = resolved["query"]

    if mode == "playlist":
        display.show_info("Enlace de Playlist detectado.")
        handle_playlist_download(query, output_dir)
    elif mode == "search":
        display.show_info(f"Búsqueda por texto: '{user_input}'. Buscando el mejor resultado...")
        handle_single_download(query, output_dir)
    else:
        display.show_info("Enlace directo de video detectado.")
        handle_single_download(query, output_dir)


def run_interactive_mode(output_dir: Path):
    """Ejecuta el menú interactivo principal de Coda con Rich."""
    display.show_banner()

    while True:
        try:
            display.show_menu()
            option = display.console.input("[bold yellow]Selecciona una opción (1-3): [/bold yellow]").strip()

            if option == "1":
                handle_download_prompt(output_dir)
            elif option == "2":
                display.show_downloads_table(output_dir)
            elif option == "3":
                display.console.print("\n[bold green]¡Gracias por usar Coda! Hasta la próxima.[/bold green]\n")
                logger.info("Cierre de sesión de Coda.")
                sys.exit(0)
            else:
                display.show_warning("Opción no válida. Por favor ingresa 1, 2 o 3.")
        except KeyboardInterrupt:
            display.console.print("\n\n[bold yellow]Interrupción detectada. Saliendo de Coda...[/bold yellow]\n")
            logger.info("Coda interrumpido por KeyboardInterrupt.")
            sys.exit(0)


def main():
    try:
        logger.info("Iniciando aplicación Coda.")
        args = parse_arguments()

        output_dir = Path(args.output).resolve() if args.output else DOWNLOADS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.query:
            display.show_banner()
            resolved = resolve_query(args.query)
            mode = resolved["mode"]
            query = resolved["query"]

            if mode == "playlist":
                handle_playlist_download(query, output_dir, requested_limit=args.limit)
            else:
                handle_single_download(query, output_dir)
        else:
            run_interactive_mode(output_dir)
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fallo crítico en main(): {e}", exc_info=True)
        display.show_error(f"Ocurrió un error crítico inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
