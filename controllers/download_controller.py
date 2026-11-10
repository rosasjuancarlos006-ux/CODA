import logging
from pathlib import Path
import time
from typing import Optional

from core.downloader import download_audio_from_youtube, download_playlist
from core.resolver import resolve_query
from ui.view_interface import ViewInterface
from utils.file_manager import cleanup_files, find_partial_download_files, scan_audio_downloads
from utils.platform_validator import (
    DEFAULT_PLATFORM,
    PLATFORM_DISPLAY_NAMES,
    check_platform_mismatch,
    detect_url_platform,
)

logger = logging.getLogger(__name__)


class DownloadController:
    """
    Central controller orchestrating interactive flows, CLI executions,
    error recovery taxonomies, cancellation cleanup, and view updates.
    """

    def __init__(self, view: ViewInterface, output_dir: Path):
        self.view = view
        self.output_dir = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_interactive_loop(self) -> None:
        """Runs the primary interactive user session loop with error resilience."""
        self.view.show_banner()

        while True:
            try:
                option = self.view.show_main_menu()

                if option == "1":
                    self.handle_interactive_download()
                elif option == "2":
                    self.handle_view_downloads()
                elif option == "3":
                    self.view.show_info("¡Gracias por usar Coda! Hasta la próxima.")
                    logger.info("User requested normal exit from interactive loop.")
                    return
                else:
                    self.view.show_warning("Opción no válida. Por favor ingresa 1, 2 o 3.")
            except KeyboardInterrupt:
                self.view.show_warning("Interrupción detectada en el menú. Saliendo de Coda...")
                logger.info("Interactive loop interrupted by KeyboardInterrupt.")
                return
            except Exception as e:
                logger.exception(f"Unexpected error in interactive loop: {e}")
                self.view.show_error(f"Error inesperado en la sesión: {e}")

    def handle_interactive_download(self) -> None:
        """
        Coordinates the 5-step interactive download sequence with contextual retries
        and graceful cancellation cleanup.
        """
        start_time = time.time()

        try:
            # Paso 1: Selección de plataforma
            platform = self.view.prompt_platform()
            platform_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)

            # Paso 2: Entrada del usuario con ciclo de reintento ante vacío y escape 'cancelar'
            user_input = ""
            while True:
                raw_input = self.view.prompt_query(platform_name)
                stripped = raw_input.strip() if raw_input else ""
                if not stripped:
                    self.view.show_warning("No ingresaste ningún texto o enlace. (Escribe 'cancelar' para volver al menú)")
                    continue
                if stripped.lower() == "cancelar":
                    self.view.show_info("Operación cancelada. Retornando al menú principal.")
                    return
                user_input = stripped
                break

            # Auto-adaptación pedagógica
            mismatch, adapted_platform = check_platform_mismatch(platform, user_input)
            if mismatch:
                self.view.show_platform_mismatch(platform, adapted_platform)
                platform = adapted_platform

            resolved = resolve_query(user_input, platform=platform)
            mode = resolved["mode"]
            query = resolved["query"]

            # Paso 3: Límite si es playlist
            limit = None
            if mode == "playlist":
                limit = self.view.prompt_playlist_limit()

            # Paso 4: Formato de audio deseado
            audio_format = self.view.prompt_audio_format(is_playlist=(mode == "playlist"))

            # Paso 5: Ejecución con progreso granular
            if mode == "playlist":
                result = download_playlist(
                    playlist_url=query,
                    output_dir=self.output_dir,
                    limit=limit or 0,
                    on_progress=self.view.on_progress,
                    audio_format=audio_format
                )

                if not result.get("success"):
                    if result.get("error") == "empty_playlist":
                        self.view.show_info("La lista de reproducción no contiene pistas descargables o está vacía.")
                    else:
                        self.view.show_error(result.get("message", "Error procesando playlist"), result.get("error"))
                else:
                    self.view.show_playlist_summary(result, self.output_dir)
            else:
                result = download_audio_from_youtube(
                    query=query,
                    output_dir=self.output_dir,
                    audio_format=audio_format,
                    on_progress=self.view.on_progress
                )

                if result.get("success"):
                    self.view.show_single_success(result)
                else:
                    self.view.show_error(result.get("message", "Error durante la descarga"), result.get("error"))

        except KeyboardInterrupt:
            logger.info("Interactive download cancelled by user. Cleaning partial files...")
            self.view.show_warning("Descarga cancelada por el usuario. Limpiando archivos parciales...")
            partials = find_partial_download_files(self.output_dir, start_time)
            cleanup_files(partials)
            self.view.show_info("Retornando al menú principal.")
        except Exception as e:
            logger.exception(f"Unexpected error in interactive download: {e}")
            self.view.show_error(f"Error inesperado durante la descarga: {e}")
        finally:
            self.view.stop_progress_task()

    def handle_view_downloads(self) -> None:
        """Scans the downloads folder and instructs the view to render results."""
        downloads = scan_audio_downloads(self.output_dir)
        if not downloads:
            self.view.show_empty_downloads()
        else:
            self.view.show_downloads_table(downloads)

    def run_cli_direct(
        self,
        query: str,
        requested_format: Optional[str] = None,
        playlist_limit: Optional[int] = None
    ) -> int:
        """
        Executes direct non-interactive download via CLI arguments.
        Returns standard exit codes (0 = success, 1 = failure, 130 = user cancellation).
        """
        start_time = time.time()
        self.view.show_banner()

        try:
            detected_platform = detect_url_platform(query)
            platform = detected_platform if detected_platform is not None else DEFAULT_PLATFORM
            logger.info(f"CLI direct execution using platform: {platform}")

            resolved = resolve_query(query, platform=platform)
            mode = resolved["mode"]
            resolved_query = resolved["query"]
            fmt = requested_format if requested_format else "mp3"

            if mode == "playlist":
                result = download_playlist(
                    playlist_url=resolved_query,
                    output_dir=self.output_dir,
                    limit=playlist_limit or 0,
                    on_progress=self.view.on_progress,
                    audio_format=fmt
                )
                if not result.get("success"):
                    self.view.show_error(result.get("message", "Error procesando playlist"), result.get("error"))
                    return 1
                self.view.show_playlist_summary(result, self.output_dir)
                return 0
            else:
                result = download_audio_from_youtube(
                    query=resolved_query,
                    output_dir=self.output_dir,
                    audio_format=fmt,
                    on_progress=self.view.on_progress
                )
                if not result.get("success"):
                    self.view.show_error(result.get("message", "Error durante la descarga"), result.get("error"))
                    return 1
                self.view.show_single_success(result)
                return 0

        except KeyboardInterrupt:
            logger.info("CLI direct execution interrupted by user.")
            self.view.show_warning("Operación directa interrumpida por el usuario.")
            partials = find_partial_download_files(self.output_dir, start_time)
            cleanup_files(partials)
            return 130
        except Exception as e:
            logger.exception(f"Error in CLI direct execution: {e}")
            self.view.show_error(f"Fallo en ejecución directa: {e}")
            partials = find_partial_download_files(self.output_dir, start_time)
            cleanup_files(partials)
            return 1
        finally:
            self.view.stop_progress_task()
