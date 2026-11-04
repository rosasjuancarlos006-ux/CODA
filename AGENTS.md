# AGENTS.md — Coda (YouTube Music Downloader)

Coda es una herramienta de terminal en Python para buscar y descargar música o playlists completas desde YouTube en formato MP3 (192 kbps) con carátula y metadatos ID3 automáticos, contando con una interfaz de usuario profesional basada en Rich.

## Stack y estructura

- **Tecnologías y versiones clave:**
  - Python 3.10+
  - `rich>=13.0.0`: Interfaz de usuario enriquecida (paneles, tablas, progress bars, spinners y banners).
  - `yt-dlp>=2024.0.0`: Motor de extracción y descarga de audio de YouTube.
  - `mutagen>=1.48.0`: Escritura de tags ID3v2 (título, artista, álbum, carátula APIC).
  - `requests>=2.31.0`: Descarga HTTP del thumbnail para la portada.
  - `pytest`: Suite de pruebas unitarias para módulos de validación y utilidades.
  - `logging`: Sistema de bitácora centralizado persistiendo en `app.log`.
  - `FFmpeg / FFprobe`: Binarios estáticos locales en Windows o instalados en el PATH.

- **Estructura de carpetas y archivos:**
  - `main.py`: Entrada principal, orquestación del modo interactivo y soporte de argumentos.
  - `config.py`: Configuraciones base y logger global (`DOWNLOADS_DIR`, `DEFAULT_AUDIO_FORMAT`, `DEFAULT_AUDIO_QUALITY`, `LOG_FILE`).
  - `app.log`: Archivo de bitácora generado en ejecución (ignorado en git).
  - `ui/`:
    - `cli.py`: Definición y parseo de argumentos por terminal (`argparse`).
    - `display.py`: Componentes visuales con Rich (banner ASCII, paneles, tablas de biblioteca y resumen).
  - `core/`:
    - `downloader.py`: Orquestación con `yt-dlp`, gestión de excepciones y logging de descargas.
    - `resolver.py`: Transforma la entrada en query/parámetros para `yt-dlp`.
  - `metadata/`:
    - `writer.py`: Limpieza de artista/título (`clean_metadata_fields`) e incrustación de ID3 (`write_id3_metadata`).
  - `utils/`:
    - `validator.py`: Expresiones regulares y clasificación del input (`video`, `playlist`, `search`).
    - `file_manager.py`: Sanitización de caracteres prohibidos en nombres de archivo para Windows.
  - `tests/`:
    - `test_validator.py`: Pruebas unitarias para clasificación y regex de URLs.
    - `test_file_manager.py`: Pruebas de sanitización de caracteres no válidos.
  - `downloads/`: Directorio local donde se guardan los archivos `.mp3` (ignorado en git).

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
  python main.py "https://www.youtube.com/playlist?list=..." -l 5
  ```
- **Ejecutar pruebas unitarias:**
  ```powershell
  pytest tests/ -v
  ```
- **Verificación sintáctica y de módulos:**
  ```powershell
  python -c "import config, core.downloader, core.resolver, metadata.writer, utils.validator, ui.cli, ui.display, main; print('Módulos cargados exitosamente')"
  ```

## Convenciones

- **Estilo de código:** PEP 8, nombres de funciones en `snake_case`, constantes en `UPPER_SNAKE_CASE` en `config.py`.
- **Tipado estricto:** Uso de type hints de Python (`pathlib.Path`, `Optional`, `Callable`, `Literal`).
- **Logging:** Usar `logger = logging.getLogger(__name__)` por módulo, registrando advertencias y fallos con niveles apropiados (`debug`, `info`, `warning`, `error`, `exception`).
- **Codificación en Windows:** Mantener `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` para evitar problemas de codificación cp1252.
- **Idioma:**
  - Interfaz de usuario y mensajes: Español.
  - Documentación del código y logs: Español/inglés contextual limpio.
- **Manejo de rutas:** Utilizar siempre `pathlib.Path`.

## Reglas de dominio / trampas conocidas

- **FFmpeg indispensable:** Sin FFmpeg no es posible extraer ni codificar streams a `.mp3`.
- **Control de excepciones:** Cada módulo debe capturar errores de red, permisos de archivo o argumentos inválidos sin crashear silenciosamente ni abortar el hilo principal.
- **Binarios y descargas en Git:** Nunca incluir `bin/`, `downloads/` ni `app.log` en el control de versiones de Git.

## Límites

- ✅ **Siempre:**
  - Validar la existencia de FFmpeg antes de ejecutar llamadas de conversión.
  - Registrar eventos clave y excepciones en `app.log`.
  - Asegurar que `pytest` pase al 100%.
  - Actualizar `MEMORY.md` al terminar cada tarea.
- ⚠️ **Pregunta antes:**
  - Añadir dependencias obligatorias a `requirements.txt`.
  - Cambiar el formato o tasa de bits predeterminada de salida.
- 🚫 **Nunca:**
  - Incluir ejecutables de `bin/` o archivos `.mp3` en commits de Git.
  - Hardcodear rutas absolutas locales (`C:\Users\...`).

## Verificación

Para verificar que los cambios funcionan correctamente antes de finalizar:
1. Ejecutar las pruebas automatizadas:
   ```powershell
   pytest tests/ -v
   ```
2. Comprobar que no hay errores de sintaxis:
   ```powershell
   python -c "import main, config, ui.display"
   ```
