# AGENTS.md — Coda (YouTube Music Downloader)

Coda es una herramienta en Python basada en la arquitectura **Modelo-Vista-Controlador (MVC)** para buscar y descargar música o playlists completas desde YouTube y YouTube Music en formato MP3, M4A u OPUS con carátula y metadatos ID3 automáticos, contando con una capa de presentación desacoplada implementada tanto en terminal mediante Rich como en escritorio gráfico mediante Flet.

## Stack y estructura

- **Tecnologías y versiones clave:**
  - Python 3.10+
  - `flet>=0.21.0` (incluyendo Flet 1.1.2+): Capa de presentación gráfica moderna y desacoplada (ejecución nativa de escritorio y web vía `flet run --web main.py`).
  - `rich>=13.0.0`: Capa de presentación enriquecida por terminal (paneles, tablas, progress bars, spinners y banners).
  - `yt-dlp>=2024.0.0`: Motor de extracción y descarga de audio de YouTube y YouTube Music.
  - `mutagen>=1.48.0`: Escritura de tags ID3v2 (título, artista, álbum, carátula APIC).
  - `requests>=2.31.0`: Descarga HTTP del thumbnail para la portada.
  - `pytest`: Suite de pruebas unitarias para módulos puros, controladores y contratos de vista.
  - `logging`: Sistema de bitácora centralizado persistiendo en `app.log`.
  - `FFmpeg / FFprobe`: Binarios estáticos locales en Windows o instalados en el PATH.

- **Estructura de carpetas y archivos (Arquitectura MVC):**
  - `main.py`: Punto de entrada unificado y minimalista (< 50 líneas). Realiza el bootstrap, parseo dual (CLI vs GUI) e inyección de dependencias (`TerminalView` + `DownloadController` o `FletView` + `GUIController`).
  - `config.py`: Configuraciones base y logger global (`DOWNLOADS_DIR`, `DEFAULT_AUDIO_FORMAT`, `DEFAULT_AUDIO_QUALITY`, `LOG_FILE`).
  - `app.log`: Archivo de bitácora generado en ejecución (ignorado en git).
  - `controllers/`:
    - `download_controller.py`: **Controlador CLI**. Orquestación del flujo interactivo por terminal y modo directo por línea de comandos.
    - `gui_controller.py`: **Controlador GUI**. Orquestación asíncrona de cola FIFO en hilo secundario daemon, cancelación activa con purga de temporales y búsqueda desacoplada.
  - `ui/`:
    - `view_interface.py`: **Contrato de Vista**. Protocolo abstracto (`ViewInterface`) desacoplado de librerías visuales concretas.
    - `terminal_view.py`: **Vista Terminal**. Implementación concreta con Rich consumiendo eventos con degradación visual.
    - `cli.py`: Definición y parseo de argumentos por terminal (`argparse`) con flags `--gui` y `--cli`.
    - `display.py`: Componentes y utilidades estéticas auxiliares con Rich.
    - `ui/gui/`:
      - `theme.py`: Tokens de diseño, paleta oscura Figma y constructor de tema Flet (`build_coda_theme`).
      - `flet_view.py`: Implementación concreta de `ViewInterface` en Flet con conmutación de paneles, gestión de ventanas y modales.
      - `views/`:
        - `sidebar.py`: Barra de navegación lateral fija (Inicio, Descargas con badge de cola, Archivos).
        - `home_view.py`: Pantalla de bienvenida, pegado de portapapeles, validación de enlace y tabla de descargas recientes.
        - `search_view.py`: Pantalla de búsqueda por texto con indicador de carga y tarjetas verticales para los 5 mejores resultados.
        - `options_view.py`: Configuración previa a la descarga (plataforma, formato, límite de playlist y confirmación).
        - `downloads_view.py`: Monitoreo en tiempo real de tarea activa, cola FIFO interactiva y tarjeta de éxito.
        - `files_view.py`: Biblioteca de audios locales escaneados en disco con botón para abrir en explorador de archivos.
  - `core/`:
    - `events.py`: **Modelo de Eventos**. DTOs inmutables (`ProgressEvent`, `DownloadPhase`) agnósticos de la UI.
    - `queue_manager.py`: **Gestor de Cola**. Estructuras inmutables puras (`QueueItem`, `QueueItemStatus`) y operaciones FIFO.
    - `downloader.py`: **Modelo**. Motor de descarga desacoplado de la interfaz con emisión de `ProgressEvent`.
    - `resolver.py`: Transforma la entrada en query/parámetros para `yt-dlp` y búsqueda ligera `buscar_top_coincidencias`.
  - `metadata/`:
    - `writer.py`: Limpieza de artista/título e incrustación de ID3 con degradación elegante.
  - `utils/`:
    - `file_manager.py`: Sanitización de nombres para Windows, resolución de colisiones (`resolve_incremental_filename`), escaneo de descargas y limpieza de temporales.
    - `platform_validator.py`: Normalización y validación pura de plataformas (`youtube`, `youtube_music`), detección de dominio y chequeo de discrepancias.
    - `validator.py`: Expresiones regulares, clasificación del input (`video`, `playlist`, `search`), poda de mixes (`clean_video_url`, `clean_mixed_url`).
    - `format_validator.py`: Normalización y validación pura de formatos de audio (`mp3`, `m4a`, `opus`).
  - `tests/`:
    - `test_gui_adapter.py`: Pruebas unitarias headless del adaptador `FletView` y conformidad del contrato `ViewInterface`.
    - `test_url_cleaner.py`: Pruebas unitarias para el analizador y podador de enlaces mixtos (`clean_mixed_url`).
    - `test_queue_manager.py`: Pruebas unitarias para el modelo y operaciones de cola FIFO.
    - `test_file_collisions.py`: Pruebas de resolución incremental de nombres y escaneo de metadatos de biblioteca.
    - `test_gui_controller.py`: Pruebas del controlador GUI, worker asíncrono y cancelación.
    - `test_theme.py`: Pruebas de tokens y paleta estética de Figma.
    - `test_flet_contracts.py`: Pruebas unitarias de integridad de contratos de datos entre vistas Flet y GUIController.
    - `test_gui_queue_concurrency.py`: Pruebas de concurrencia y sincronización FIFO en el worker asíncrono de GUI.
    - `test_sidebar.py`, `test_home_view.py`, `test_search_view.py`, `test_options_view.py`, `test_downloads_view.py`, `test_files_view.py`, `test_flet_view.py`: Pruebas unitarias de componentes Flet.
    - `test_controller.py`: Pruebas unitarias de orquestación CLI con `FakeView` en memoria.
    - `test_terminal_view.py`: Pruebas de la implementación concreta de la vista de terminal.
    - `test_view_interface.py`: Pruebas de conformidad y rechazo estructural del contrato `ViewInterface`.
    - `test_events.py`: Pruebas de instanciación, inmutabilidad y clamping de `ProgressEvent`.
    - `test_downloader_events.py`: Pruebas de emisión de eventos de progreso en el motor de descarga.
    - `test_constitution.py`: Pruebas de enmiendas de gobernanza de la Constitución.
    - `test_platform_validator.py`: Pruebas unitarias para alias de plataforma, normalización y detección de URLs.
    - `test_validator.py`: Pruebas unitarias para clasificación y regex de URLs.
    - `test_resolver.py`: Pruebas unitarias para resolución contextual de búsquedas y top 5 resultados.
    - `test_display_platform.py`: Pruebas unitarias para componentes visuales de plataforma con mocks.
    - `test_main_orchestration.py`: Pruebas unitarias del bootstrap dual en `main.py`.
    - `test_format_validator.py`: Pruebas unitarias para validación y normalización de formatos.
    - `test_core_validators.py`: Pruebas exhaustivas de validadores puros, clasificación, alias y sanitización de archivos.
    - `test_core_queue_events.py`: Pruebas exhaustivas de eventos inmutables y operaciones puras de cola FIFO.
    - `test_core_downloader_isolated.py`: Pruebas unitarias de resolución contextual y motor desacoplado con mocks.
    - `test_integration_ffmpeg_detection.py`: Pruebas de integración para detección y jerarquía de FFmpeg.
    - `test_integration_transcode.py`: Pruebas de integración para transcodificación sintética a MP3, M4A y OPUS.
    - `test_integration_daemon_pipes.py`: Pruebas de integración para ejecución en hilos daemon sin TTY.
    - `test_integration_temp_cleanup.py`: Pruebas de integración de rutas Windows y purga atómica de temporales.
    - `test_core_metadata_writer.py`: Pruebas de inyección ID3v2, parsing de artistas y degradación elegante en M4A/OPUS.
    - `test_ui_progress_throttling.py`: Pruebas de throttling de eventos de alta frecuencia y thread-safety de safe_update en Flet.
    - `test_gui_lifecycle_cancel.py`: Pruebas de ciclo de vida: cancelación activa con purga de temporales, modales y cierre de ventana.
    - `test_file_manager.py`: Pruebas de sanitización, filtrado de extensiones y detección de temporales.
    - `test_qa_edge_cases.py`: Pruebas de timeouts de red en yt-dlp, integridad de ID3 y carátulas WebP.
  - `downloads/`: Directorio local donde se guardan los archivos de audio (ignorado en git).

## Comandos

- **Instalar dependencias:**
  ```powershell
  pip install -r requirements.txt
  ```
- **Ejecutar la interfaz gráfica (Modo GUI de escritorio o web):**
  ```powershell
  python main.py
  python main.py --gui
  flet run --web main.py
  ```
- **Ejecutar la interfaz de terminal interactiva:**
  ```powershell
  python main.py --cli
  ```
- **Ejecutar con argumentos directos por terminal:**
  ```powershell
  python main.py "Nombre de cancion"
  python main.py "https://music.youtube.com/watch?v=..."
  python main.py "https://www.youtube.com/playlist?list=..." -l 5
  ```
- **Ejecutar pruebas unitarias:**
  ```powershell
  pytest tests/ -v
  ```
- **Verificación sintáctica y de módulos:**
  ```powershell
  python -c "import config, core.downloader, core.resolver, core.events, core.queue_manager, controllers.download_controller, controllers.gui_controller, ui.view_interface, ui.terminal_view, ui.gui.flet_view, metadata.writer, utils.validator, utils.platform_validator, utils.format_validator, utils.file_manager, ui.cli, ui.display, main; print('Módulos cargados exitosamente')"
  ```

## Convenciones

- **Estilo de código:** PEP 8, nombres de funciones en `snake_case`, constantes en `UPPER_SNAKE_CASE` en `config.py` y validadores.
- **Tipado estricto:** Uso de type hints de Python (`pathlib.Path`, `Optional`, `Callable`, `Literal`, `Tuple`, `Protocol`).
- **Logging:** Usar `logger = logging.getLogger(__name__)` por módulo, registrando en inglés advertencias y fallos (`debug`, `info`, `warning`, `error`, `exception`).
- **Codificación en Windows:** Mantener `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` para evitar problemas de codificación cp1252.
- **Idioma:**
  - Interfaz de usuario y mensajes: Español.
  - Documentación del código y logs: Inglés.
- **Manejo de rutas:** Utilizar siempre `pathlib.Path`.

## Reglas de dominio / trampas conocidas

- **FFmpeg indispensable:** Sin FFmpeg no es posible extraer ni codificar streams a `.mp3`, `.m4a` u `.opus`.
- **Control de excepciones y degradación:** La inyección de metadatos o carátula no soportada en formatos no MP3 no debe abortar la descarga; el audio se conserva intacto.
- **Mixes de YouTube Music:** Los enlaces tipo `watch?v=ID&list=RD...` deben clasificarse como `video` y sanearse mediante `clean_video_url` o `clean_mixed_url` para evitar descargas accidentales infinitas.
- **Binarios y descargas en Git:** Nunca incluir `bin/`, `downloads/` ni `app.log` en el control de versiones de Git.

## Reglas
- Lee `docs/constitution.md` y la spec activa (`specs/NNN-*/`) antes de tocar código.

## Límites

- ✅ **Siempre:**
  - Validar la existencia de FFmpeg antes de ejecutar llamadas de conversión.
  - Registrar eventos clave y excepciones en `app.log`.
  - Asegurar que `pytest` pase al 100%.
  - Actualizar `MEMORY.md` al terminar cada tarea.
- ⚠️ **Pregunta antes:**
  - Añadir dependencias obligatorias a `requirements.txt`.
  - Modificar formatos permitidos o tasa de bits por defecto.
- 🚫 **Nunca:**
  - Incluir ejecutables de `bin/` o archivos de audio en commits de Git.
  - Hardcodear rutas absolutas locales (`C:\Users\...`).

## Verificación

Para verificar que los cambios funcionan correctamente antes de finalizar:
1. Ejecutar las pruebas automatizadas:
   ```powershell
   pytest tests/ -v
   ```
2. Comprobar que no hay errores de sintaxis:
   ```powershell
   python -c "import main, config, ui.terminal_view, ui.gui.flet_view, controllers.download_controller, controllers.gui_controller, utils.platform_validator"
   ```
