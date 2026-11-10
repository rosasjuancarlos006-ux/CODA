# Tareas de Implementación — Arquitectura Modelo-Vista-Controlador (003-MVC)

Lista de tareas secuenciales organizadas por dependencias lógicas. Cada tarea está acotada para completarse en un intervalo de 20 a 30 minutos y cuenta con su respectivo mapeo a los Requisitos Funcionales (RF) y un criterio de aceptación verificable mediante comando.

---

### Tarea 1: Enmienda formal de gobernanza en la Constitución
- **Archivo:** `docs/constitution.md`
- **Requisitos cubiertos:** Criterio de Finalización 1, RNF-01
- **Descripción:** Actualizar formalmente la Regla 4 de `docs/constitution.md` para autorizar pruebas unitarias del controlador y contratos de presentación utilizando vistas simuladas en memoria (*mocks*/*fakes* de la biblioteca estándar), manteniendo la restricción de cero dependencias externas de prueba.
- [x] **Hecho cuando:** `python -c "text = open('docs/constitution.md', encoding='utf-8').read().lower(); assert 'controlador' in text and 'mocks' in text; print('Enmienda verificada')"` se ejecute con salida 0.

---

### Tarea 2: Modelo neutro de eventos de descarga y progreso
- **Archivos:** `core/events.py`, `tests/test_events.py`
- **Requisitos cubiertos:** RF-01, RF-05, RNF-02
- **Descripción:** Crear el módulo `core/events.py` con el enumerador `DownloadPhase` (`PREPARING`, `DOWNLOADING`, `CONVERTING`, `METADATA`, `COMPLETED`, `ERROR`) y la dataclass inmutable `ProgressEvent` (almacenando fase, porcentaje, velocidad, tiempo estimado, elemento actual y total). Implementar la función auxiliar `create_progress_event`. Crear `tests/test_events.py` para validar instanciación, valores por defecto e inmutabilidad.
- [x] **Hecho cuando:** `pytest tests/test_events.py -v` pase al 100% en todos sus casos.

---

### Tarea 3: Utilidades de escaneo de biblioteca y limpieza de residuos parciales
- **Archivos:** `utils/file_manager.py`, `tests/test_file_manager.py`
- **Requisitos cubiertos:** RF-03, RF-06, RNF-03
- **Descripción:** Añadir en `utils/file_manager.py` la dataclass `AudioFileInfo`, la constante `SUPPORTED_AUDIO_EXTENSIONS` (`{".mp3", ".m4a", ".opus"}`), y las funciones puras `scan_audio_downloads` (filtrado de audios ordenados por fecha), `find_partial_download_files` (detección de temporales huérfanos por timestamp) y `cleanup_files` (eliminación segura sin excepciones). Añadir pruebas unitarias exhaustivas en `tests/test_file_manager.py`.
- [x] **Hecho cuando:** `pytest tests/test_file_manager.py -v` pase al 100% verificando el filtrado de extensiones y la detección de archivos huérfanos.

---

### Tarea 4: Definición del contrato abstracto de presentación (`ViewInterface`)
- **Archivo:** `ui/view_interface.py`
- **Requisitos cubiertos:** RF-01, RF-05, RF-06, RNF-02
- **Descripción:** Crear el protocolo estructural `ViewInterface(Protocol)` definiendo las firmas de todos los métodos requeridos por la vista: despliegue de menús (`show_banner`, `show_main_menu`), prompts interactivos (`prompt_platform`, `prompt_query`, `prompt_playlist_limit`, `prompt_audio_format`), avisos (`show_platform_mismatch`, `show_info`, `show_warning`, `show_error`), resúmenes (`show_single_success`, `show_playlist_summary`), biblioteca local (`show_downloads_table`, `show_empty_downloads`) y reporte de progreso (`on_progress`).
- [x] **Hecho cuando:** `python -c "from ui.view_interface import ViewInterface; from typing import runtime_checkable; print('ViewInterface cargada exitosamente')"` se ejecute sin errores.

---

### Tarea 5: Implementación de la vista para terminal (`TerminalView`) y degradación visual
- **Archivos:** `ui/terminal_view.py`, `ui/display.py`
- **Requisitos cubiertos:** RF-01, RF-05, RF-06, RF-07, RNF-04
- **Descripción:** Implementar la clase `TerminalView` satisfaciendo estructuralmente `ViewInterface` usando `rich`. Conectar `on_progress` con barras de progreso y spinners, aplicando degradación visual a indicadores indeterminados cuando falten métricas de velocidad o porcentaje. Implementar `show_downloads_table` con tabla formateada y `show_empty_downloads` con mensaje informativo amigable. Adaptar `ui/display.py` para mantener compatibilidad con utilidades estéticas compartidas.
- [x] **Hecho cuando:** `python -c "from ui.terminal_view import TerminalView; from ui.view_interface import ViewInterface; view = TerminalView(); print('TerminalView satisface ViewInterface')"` se ejecute con salida exitosa.

---

### Tarea 6: Emisión de eventos desacoplados en el motor de descarga
- **Archivo:** `core/downloader.py`
- **Requisitos cubiertos:** RF-03, RF-05, RNF-02, RNF-03
- **Descripción:** Modificar `download_audio_from_youtube` y `download_playlist` en `core/downloader.py` para que acepten un callback `on_progress: Optional[Callable[[ProgressEvent], None]]`, transformando los hooks nativos de `yt-dlp` en instancias de `ProgressEvent`. Eliminar cualquier import o referencia a `rich` o elementos de interfaz dentro de `downloader.py`.
- [x] **Hecho cuando:** `python -c "import core.downloader; assert 'rich' not in [name for name in dir(core.downloader) if not name.startswith('_')]; print('Downloader desacoplado de la interfaz')"` finalice con código de salida 0.

---

### Tarea 7: Controlador central de la aplicación (`DownloadController`)
- **Archivo:** `controllers/download_controller.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07
- **Descripción:** Implementar `DownloadController(view: ViewInterface, output_dir: Path)`. Codificar `run_interactive_loop()` con bucle resiliente ante errores; `handle_interactive_download()` con la secuencia estricta de 5 pasos, opción de escape `'cancelar'` y captura de `KeyboardInterrupt` que suprime temporales vía `find_partial_download_files`; `handle_view_downloads()` con escaneo y llamada a la vista; y `run_cli_direct()` retornando códigos de salida estándar (0 en éxito, 1 en error, 130 en cancelación).
- [x] **Hecho cuando:** `python -c "from controllers.download_controller import DownloadController; print('DownloadController cargado exitosamente')"` se ejecute con código 0.

---

### Tarea 8: Pruebas unitarias de orquestación del controlador con `FakeView`
- **Archivo:** `tests/test_controller.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-03, RF-04, RF-07
- **Descripción:** Crear `FakeView` en memoria y escribir la suite de pruebas automatizadas para `DownloadController`:
  1. Ejecución CLI directa exitosa (código 0).
  2. Ejecución CLI directa con fallo operativo (código 1 y limpieza de temporales).
  3. Ejecución CLI directa interrumpida por Ctrl+C (código 130 y limpieza de temporales).
  4. Bucle interactivo ante entrada vacía (reintento sin cerrar el programa).
  5. Bucle interactivo con comando 'cancelar' (retorno al menú principal).
  6. Interrupción con Ctrl+C durante descarga interactiva (limpieza y retorno al menú).
  7. Detección de playlist vacía o sin pistas disponibles (aviso informativo y retorno al menú).
  8. Ausencia de FFmpeg en interactivo (diagnóstico en español y retorno al menú).
- [x] **Hecho cuando:** `pytest tests/test_controller.py -v` ejecute al menos 8 pruebas y todas pasen al 100%.

---

### Tarea 9: Refactorización del punto de entrada `main.py` (Bootstrap)
- **Archivo:** `main.py`
- **Requisitos cubiertos:** RF-01, RF-04
- **Descripción:** Reducir `main.py` a un bootstrap mínimo (< 35 líneas). Parsear argumentos de `ui/cli.py`, resolver la ruta de descargas, crear la instancia de `TerminalView()`, ensamblar `DownloadController(view, output_dir)` y despachar hacia `controller.run_cli_direct(...)` o `controller.run_interactive_loop()`. Eliminar de `main.py` toda lógica de orquestación, prompts directos y renderizado.
- [x] **Hecho cuando:** `python main.py -h` imprima el menú de ayuda sin errores y `python -c "import main; print('main.py verificado')"` finalice exitosamente.

---

### Tarea 10: Actualización de arquitectura en `AGENTS.md`, bitácora y verificación global
- **Archivos:** `AGENTS.md`, `MEMORY.md`
- **Requisitos cubiertos:** Criterio de Finalización 2, no regresión general
- **Descripción:** Actualizar `AGENTS.md` reflejando la nueva estructura modular (`controllers/`, `ui/view_interface.py`, `ui/terminal_view.py`, `core/events.py`) y la nueva regla de tests del controlador. Registrar aprendizajes y decisiones en `MEMORY.md`. Ejecutar la suite completa de pruebas unitarias para constatar cero regresiones.
- [x] **Hecho cuando:** `pytest tests/ -v` pase al 100% en todas las suites de prueba (superando 55 tests unitarios en total) y la verificación de sintaxis de todos los módulos sea satisfactoria.
