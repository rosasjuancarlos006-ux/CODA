import logging
import sys
from pathlib import Path

from config import DOWNLOADS_DIR
from controllers.download_controller import DownloadController
from ui.cli import parse_arguments
from ui.terminal_view import TerminalView

logger = logging.getLogger("coda.main")


def main() -> None:
    try:
        logger.info("Iniciando aplicación Coda.")
        args = parse_arguments()
        output_dir = Path(args.output).resolve() if args.output else DOWNLOADS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        view = TerminalView()
        controller = DownloadController(view=view, output_dir=output_dir)

        if args.query:
            exit_code = controller.run_cli_direct(
                query=args.query,
                requested_format=args.format,
                playlist_limit=args.limit
            )
            sys.exit(exit_code)
        else:
            controller.run_interactive_loop()
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fallo crítico en main(): {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
