# Tareas de Implementación — Soporte Multiplataforma (002-platform)

Lista de tareas secuenciales organizadas por dependencias lógicas. Cada tarea está acotada para completarse en un intervalo de 20-30 minutos y cuenta con un criterio verificable de aceptación.

---

### Tarea 1: Módulo puro de validación y normalización de plataformas
- **Archivo:** `utils/platform_validator.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-05
- **Descripción:** Implementar las constantes (`SUPPORTED_PLATFORMS`, `DEFAULT_PLATFORM`, `PLATFORM_DISPLAY_NAMES`), la función pura `normalize_platform_input` (colapsando espacios y normalizando alias), `detect_url_platform` para identificar el dominio de una URL, y `check_platform_mismatch` para la auto-adaptación sin efectos secundarios.
- [x] **Hecho cuando:** `python -c "from utils.platform_validator import normalize_platform_input, detect_url_platform, check_platform_mismatch; assert normalize_platform_input('  yt_music  ') == (True, 'youtube_music'); assert detect_url_platform('https://music.youtube.com/watch?v=123') == 'youtube_music'; assert check_platform_mismatch('youtube', 'https://music.youtube.com/watch?v=123') == (True, 'youtube_music')"` se ejecute sin errores.

---

### Tarea 2: Suite de pruebas unitarias para el validador de plataformas
- **Archivo:** `tests/test_platform_validator.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-05
- **Descripción:** Crear suite de pruebas con `pytest` que verifique alias de YouTube (`1`, `yt`, `youtube`), alias de YouTube Music (`2`, `music`, `ytmusic`, colapso de espacios múltiples), entradas vacías/default, opciones inválidas (`spotify`, `3`), detección de dominios por URL y detección de discrepancias para auto-adaptación.
- [x] **Hecho cuando:** `pytest tests/test_platform_validator.py -v` ejecute al menos 6 tests y todos pasen al 100%.

---

### Tarea 3: Soporte de URLs de YouTube Music y saneamiento de mixes en validator
- **Archivos:** `utils/validator.py`, `tests/test_validator.py`
- **Requisitos cubiertos:** RF-03
- **Descripción:** Actualizar expresiones regulares y lógica en `utils/validator.py` para reconocer `music.youtube.com`. Implementar la función pura `clean_video_url` para podar parámetros de mix/radio (`&list=RD...`) en URLs de video individual. Añadir pruebas en `tests/test_validator.py` que verifiquen tracks de YouTube Music, playlists puras y la prioridad de track individual sobre mixes.
- [x] **Hecho cuando:** `pytest tests/test_validator.py -v` pase al 100% incluyendo los nuevos casos de YouTube Music y poda de mixes.

---

### Tarea 4: Resolución de consultas y búsqueda contextual por catálogo
- **Archivo:** `core/resolver.py`
- **Requisitos cubiertos:** RF-03, RF-04
- **Descripción:** Añadir el parámetro `platform: str = "youtube"` a `resolve_query`. Si la consulta es texto libre y la plataforma es `youtube_music`, anteponer `ytsearch1:{query} Audio Oficial` para priorizar temas de estudio. Si la consulta es una URL de video individual, aplicar `clean_video_url` para sanear la query antes de enviarla a `yt-dlp`.
- [x] **Hecho cuando:** `python -c "from core.resolver import resolve_query; res_m = resolve_query('Coldplay Yellow', platform='youtube_music'); assert 'Audio Oficial' in res_m['query']; res_v = resolve_query('https://music.youtube.com/watch?v=ABC&list=RDABC', platform='youtube_music'); assert '&list=' not in res_v['query']"` retorne exitoso.

---

### Tarea 5: Componente interactivo de plataforma y advertencia visual en Rich
- **Archivo:** `ui/display.py`
- **Requisitos cubiertos:** RF-01, RF-05
- **Descripción:** Implementar en `ui/display.py` la función `prompt_platform() -> str` con menú interactivo `[1] YouTube` y `[2] YouTube Music`, manejo de hasta 3 reintentos, captura de `KeyboardInterrupt` y fallback a `"youtube"`. Añadir helper `get_platform_display_name(platform: str) -> str` y la función `show_platform_mismatch_warning(selected: str, detected: str)` para desplegar el aviso pedagógico de auto-adaptación en español.
- [x] **Hecho cuando:** Una prueba con mock de `prompt_platform` retorne `"youtube"` con entrada vacía, `"youtube_music"` con entrada `"2"`, y `"youtube"` por defecto tras 3 intentos inválidos consecutivos.

---

### Tarea 6: Orquestación del flujo lineal en `main.py` (Interactivo y CLI)
- **Archivo:** `main.py`
- **Requisitos cubiertos:** RF-01, RF-02, RF-05, RF-06
- **Descripción:** En modo interactivo (`handle_download_prompt`), orquestar la secuencia estricta: 1. `prompt_platform` ➔ 2. Solicitud de URL/texto con chequeo de discrepancia y auto-adaptación ➔ 3. Límite de playlist (si aplica) ➔ 4. `prompt_audio_format` ➔ 5. Descarga. En ejecuciones directas por CLI (`args.query`), inferir automáticamente la plataforma vía `detect_url_platform` sin desplegar el prompt de selección.
- [x] **Hecho cuando:** Al ejecutar `python main.py "https://music.youtube.com/watch?v=123"` el sistema procese automáticamente en modo YouTube Music sin solicitar plataforma, y en modo interactivo el selector de plataforma aparezca antes de pedir el enlace.

---

### Tarea 7: Verificación integral y actualización de documentación
- **Archivos:** `AGENTS.md`, `MEMORY.md`, `README.md`
- **Requisitos cubiertos:** RF-01, RF-02, RF-03, RF-04, RF-05, RF-06
- **Descripción:** Ejecutar la suite completa de pruebas unitarias (`pytest tests/ -v`), verificar sintaxis de todos los módulos, y actualizar la documentación (`AGENTS.md`, `MEMORY.md` y `README.md`) reflejando el soporte para YouTube Music, la auto-adaptación de enlaces y las pruebas unitarias.
- [x] **Hecho cuando:** `pytest tests/ -v` pase al 100% con todos los tests del proyecto y `python -c "import main, config, ui.display, utils.platform_validator"` finalice con código de salida 0.
