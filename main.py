import logging, sys
from pathlib import Path
from config import DOWNLOADS_DIR
from controllers.download_controller import DownloadController
from ui.cli import parse_arguments
from ui.terminal_view import TerminalView

logger = logging.getLogger("coda.main")


def launch_gui(output_dir: Path) -> None:
    """Arranca la interfaz gráfica (Flet) ensamblando FletView y GUIController."""
    import flet as ft
    from controllers.gui_controller import GUIController
    from ui.gui.flet_view import FletView

    def app_main(page: ft.Page):
        view = FletView()
        ctrl = GUIController(view=view, output_dir=output_dir)
        view.set_controller(ctrl)
        view.init_page(page)

    (ft.run if hasattr(ft, "run") else ft.app)(target=app_main) if not hasattr(ft, "run") else ft.run(app_main)


def main() -> None:
    try:
        logger.info("Iniciando aplicación Coda.")
        args = parse_arguments()
        output_dir = Path(args.output).resolve() if args.output else DOWNLOADS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.query:
            ctrl = DownloadController(view=TerminalView(), output_dir=output_dir)
            sys.exit(ctrl.run_cli_direct(query=args.query, requested_format=args.format, playlist_limit=args.limit))
        elif getattr(args, "cli", False):
            DownloadController(view=TerminalView(), output_dir=output_dir).run_interactive_loop()
        else:
            launch_gui(output_dir)
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fallo crítico en main(): {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
