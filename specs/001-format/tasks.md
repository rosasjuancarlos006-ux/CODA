# Tareas de Implementación — Selección de Formato de Audio (001-format)

Lista de tareas secuenciales organizadas por dependencias lógicas. Cada tarea está acotada para completarse en un intervalo de 20-30 minutos y cuenta con un criterio verificable de aceptación.

---

### Tarea 1: Módulo puro de validación y normalización de formatos
- **Archivo:** `utils/format_validator.py`
- **Requisitos cubiertos:** RF-02, RF-03
- **Descripción:** Implementar la tupla de formatos soportados (`mp3`, `m4a`, `opus`), el formato por defecto (`mp3`) y las funciones puras `normalize_format_input`, `is_valid_format` y `resolve_audio_format`. No debe tener dependencias de UI ni efectos secundarios de I/O.
- [x] **Hecho cuando:** `python -c "from utils.format_validator import resolve_audio_format; assert resolve_audio_format('  M4A  ') == (True, 'm4a'); assert resolve_audio_format('') == (True, 'mp3'); assert resolve_audio_format('flac') == (False, '')"` se ejecute sin errores.

---

### Tarea 2: Suite de pruebas unitarias para el validador de formato
- **Archivo:** `tests/test_format_validator.py`
- **Requisitos cubiertos:** RF-02, RF-03
- **Descripción:** Crear pruebas con `pytest` que verifiquen entradas válidas, normalización de mayúsculas/espacios, entradas vacías (default `mp3`), formatos inválidos (`flac`, `wav`), cadenas largas y casos límite con `None`.
- [x] **Hecho cuando:** `pytest tests/test_format_validator.py -v` ejecute al menos 8 tests y todos pasen al 100%.

---

### Tarea 3: Soporte de formato dinámico en el motor de descarga
- **Archivo:** `core/downloader.py`
- **Requisitos cubiertos:** RF-04
- **Descripción:** Modificar `download_audio_from_youtube` para recibir el parámetro `audio_format: str = "mp3"`, configurar el postprocesador `FFmpegExtractAudio` con `preferredcodec: audio_format` y adaptar la búsqueda del archivo resultante en `downloads/` a `*.{audio_format}`. Propagar el parámetro en `download_playlist`.
- [x] **Hecho cuando:** `python -c "import inspect; from core.downloader import download_audio_from_youtube, download_playlist; assert 'audio_format' in inspect.signature(download_audio_from_youtube).parameters; assert 'audio_format' in inspect.signature(download_playlist).parameters"` retorne exitoso.

---

### Tarea 4: Tolerancia y degradación elegante en inyección de metadatos
- **Archivo:** `metadata/writer.py`
- **Requisitos cubiertos:** RF-05
- **Descripción:** Adaptar la lógica de metadatos para admitir archivos no MP3 (`m4a`, `opus`). Si la incrustación de tags o carátula no es soportada nativamente o falla, capturar la excepción, emitir log `warning` en inglés y retornar `False` (o dict de estado) sin lanzar error fatal ni alterar el archivo de audio descargado.
- [x] **Hecho cuando:** Una llamada simulada con un archivo de prueba `.opus` o `.m4a` no genere excepciones no controladas y preserve la integridad del archivo en disco.

---

### Tarea 5: Componente visual de selección y reintentos en Rich
- **Archivo:** `ui/display.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-03, RF-05
- **Descripción:** Implementar la función interactiva `prompt_audio_format(is_playlist: bool = False) -> str` en `ui/display.py` utilizando `rich.console`. Debe mostrar la advertencia si es playlist, consultar el formato con el prompt definido, manejar hasta 3 reintentos antes de seleccionar `mp3` por defecto, registrar logs en inglés y capturar `KeyboardInterrupt`. Actualizar `show_success_single` y `show_downloads_table` para reflejar el formato elegido.
- [x] **Hecho cuando:** Al invocar `prompt_audio_format` en prueba interactiva o mock, una entrada vacía retorne `"mp3"`, una entrada `"opus"` retorne `"opus"`, y 3 entradas inválidas consecutivas emitan la advertencia de límite y retornen `"mp3"`.

---

### Tarea 6: Orquestación del flujo en `main.py` (Interactivo y CLI)
- **Archivo:** `main.py`
- **Requisitos cubiertos:** RF-01, RF-04
- **Descripción:** Conectar `prompt_audio_format` en `handle_download_prompt` (canciones individuales y búsquedas) y en `handle_playlist_download` (después de preguntar el límite de canciones). En ejecuciones directas con argumento CLI (`args.query`), solicitar interactivamente el formato antes de invocar la descarga.
- [x] **Hecho cuando:** Al ejecutar `python main.py "The Beatles Yesterday"` o seleccionar opción 1 en el menú interactivo, la aplicación solicite el formato antes de iniciar la conversión y pase el formato elegido a `download_audio_from_youtube`.

---

### Tarea 7: Verificación integral y actualización de documentación
- **Archivos:** `AGENTS.md`, `MEMORY.md`
- **Requisitos cubiertos:** RF-01, RF-02, RF-03, RF-04, RF-05
- **Descripción:** Ejecutar la suite completa de pruebas (`pytest tests/ -v`), comprobar sintaxis de todos los módulos, y actualizar `AGENTS.md` y `MEMORY.md` registrando la nueva capacidad multiformato (`mp3`, `m4a`, `opus`), decisiones técnicas y lecciones aprendidas.
- [x] **Hecho cuando:** `pytest tests/ -v` pase al 100% con todos los tests del proyecto y `python -c "import main, config, ui.display"` finalice con código de salida 0.
