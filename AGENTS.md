# AGENTS.md — Coda (YouTube Music Downloader)

Coda es una herramienta de terminal en Python para buscar y descargar música o playlists completas desde YouTube y YouTube Music en formato MP3, M4A u OPUS con carátula y metadatos ID3 automáticos, contando con una interfaz de usuario profesional basada en Rich.

## Stack y estructura

- **Tecnologías y versiones clave:**
  - Python 3.10+
  - `rich>=13.0.0`: Interfaz de usuario enriquecida (paneles, tablas, progress bars, spinners y banners).
  - `yt-dlp>=2024.0.0`: Motor de extracción y descarga de audio de YouTube y YouTube Music.
  - `mutagen>=1.48.0`: Escritura de tags ID3v2 (título, artista, álbum, carátula APIC).
  - `requests>=2.31.0`: Descarga HTTP del thumbnail para la portada.
  - `pytest`: Suite de pruebas unitarias para módulos de validación y utilidades.
  - `logging`: Sistema de bitácora centralizado persistiendo en `app.log`.
  - `FFmpeg / FFprobe`: Binarios estáticos locales en Windows o instalados en el PATH.

- **Estructura de carpetas y archivos:**
  - `main.py`: Entrada principal, orquestación del flujo lineal interactivo y soporte de argumentos CLI.
  - `config.py`: Configuraciones base y logger global (`DOWNLOADS_DIR`, `DEFAULT_AUDIO_FORMAT`, `DEFAULT_AUDIO_QUALITY`, `LOG_FILE`).
  - `app.log`: Archivo de bitácora generado en ejecución (ignorado en git).
  - `ui/`:
    - `cli.py`: Definición y parseo de argumentos por terminal (`argparse`).
    - `display.py`: Componentes visuales con Rich (banner, selector interactivo de plataforma, prompt de formato con reintentos, tablas y resumen).
  - `core/`:
    - `downloader.py`: Orquestación con `yt-dlp` (formato dinámico mp3/m4a/opus), gestión de excepciones y logging.
    - `resolver.py`: Transforma la entrada en query/parámetros para `yt-dlp` según plataforma contextual y sanea URLs individuales.
  - `metadata/`:
    - `writer.py`: Limpieza de artista/título e incrustación de ID3 con degradación elegante.
  - `utils/`:
    - `platform_validator.py`: Normalización y validación pura de plataformas (`youtube`, `youtube_music`), detección de dominio y chequeo de discrepancias.
    - `validator.py`: Expresiones regulares, clasificación del input (`video`, `playlist`, `search`) y poda de mixes (`clean_video_url`).
    - `format_validator.py`: Normalización y validación pura de formatos de audio (`mp3`, `m4a`, `opus`).
    - `file_manager.py`: Sanitización de caracteres prohibidos en nombres de archivo para Windows.
  - `tests/`:
    - `test_platform_validator.py`: Pruebas unitarias para alias de plataforma, normalización y detección de URLs.
    - `test_validator.py`: Pruebas unitarias para clasificación y regex de URLs (YouTube y YouTube Music).
    - `test_resolver.py`: Pruebas unitarias para resolución contextual de búsquedas y poda de URLs.
    - `test_display_platform.py`: Pruebas unitarias para componentes visuales de plataforma con mocks.
    - `test_main_orchestration.py`: Pruebas unitarias del flujo de orquestación (interactivo y CLI).
    - `test_format_validator.py`: Pruebas unitarias para validación y normalización de formatos.
    - `test_file_manager.py`: Pruebas de sanitización de caracteres no válidos.
  - `downloads/`: Directorio local donde se guardan los archivos de audio (ignorado en git).

## Comandos

- **Instalar dependencias:**
  ```powershell
  pip install -r requirements.txt
  ```
- **Ejecutar la aplicación (Modo interactivo):**
  ```powershell
  python main.py
  ```
- **Ejecutar con argumentos directos:**
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
  python -c "import config, core.downloader, core.resolver, metadata.writer, utils.validator, utils.platform_validator, utils.format_validator, ui.cli, ui.display, main; print('Módulos cargados exitosamente')"
  ```

## Convenciones

- **Estilo de código:** PEP 8, nombres de funciones en `snake_case`, constantes en `UPPER_SNAKE_CASE` en `config.py` y validadores.
- **Tipado estricto:** Uso de type hints de Python (`pathlib.Path`, `Optional`, `Callable`, `Literal`, `Tuple`).
- **Logging:** Usar `logger = logging.getLogger(__name__)` por módulo, registrando en inglés advertencias y fallos (`debug`, `info`, `warning`, `error`, `exception`).
- **Codificación en Windows:** Mantener `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` para evitar problemas de codificación cp1252.
- **Idioma:**
  - Interfaz de usuario y mensajes: Español.
  - Documentación del código y logs: Inglés.
- **Manejo de rutas:** Utilizar siempre `pathlib.Path`.

## Reglas de dominio / trampas conocidas

- **FFmpeg indispensable:** Sin FFmpeg no es posible extraer ni codificar streams a `.mp3`, `.m4a` u `.opus`.
- **Control de excepciones y degradación:** La inyección de metadatos o carátula no soportada en formatos no MP3 no debe abortar la descarga; el audio se conserva intacto.
- **Mixes de YouTube Music:** Los enlaces tipo `watch?v=ID&list=RD...` deben clasificarse como `video` y sanearse mediante `clean_video_url` para evitar descargas accidentales infinitas.
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
   python -c "import main, config, ui.display, utils.platform_validator"
   ```
