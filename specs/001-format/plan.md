# Plan de Implementación Técnica — Selección de Formato de Audio (001-format)

Este documento detalla la arquitectura, algoritmos, interfaz, decisiones técnicas y suite de pruebas para implementar la especificación de `specs/001-format/spec.md`, en conformidad total con `docs/constitution.md`.

---

## 1. Archivos a crear o modificar y sus responsabilidades

| Archivo | Estado | Responsabilidad y cambios previstos | RF Cubiertos |
| :--- | :--- | :--- | :--- |
| **`utils/format_validator.py`** | **Crear** | **Lógica pura y desacoplada**: Contiene la definición de formatos permitidos, la normalización de cadenas de entrada y la función pura que valida si una entrada es admisible o retorna el valor por defecto. Sin I/O ni interacción de consola. | **RF-02**, **RF-03** |
| **`ui/display.py`** | **Modificar** | **Capa de presentación**: Función interactiva para solicitar el formato al usuario (`prompt_audio_format`), renderizado de advertencias de formatos no válidos, control de los 3 reintentos antes del fallback a `mp3`, y reporte de advertencias diferenciadas sobre metadatos/portada. | **RF-01**, **RF-02**, **RF-03**, **RF-05** |
| **`core/downloader.py`** | **Modificar** | **Motor de descarga**: Añadir parámetro `audio_format: str = "mp3"` a `download_audio_from_youtube` y propagarlo desde `download_playlist`. Configurar dinámicamente `preferredcodec` en `FFmpegExtractAudio` de `yt-dlp` (`mp3`, `m4a`, `opus`) y buscar el archivo resultante con la extensión correspondiente. | **RF-04** |
| **`metadata/writer.py`** | **Modificar** | **Inyección de metadatos con degradación elegante**: Actualizar `write_id3_metadata` (o crear `write_audio_metadata`) para admitir la ruta de cualquier formato. Para `mp3` inyecta ID3 con `mutagen.easyid3` y portada APIC; para `m4a` u `opus`, si el soporte de carátula/tags no es nativo o falla, degradar limpiamente retornando un dict/status con advertencia explicativa sin corromper el audio. | **RF-05** |
| **`main.py`** | **Modificar** | **Orquestación**: Invocar la solicitud interactiva de formato a través de `ui/display.py` antes de iniciar la descarga (tanto en canciones individuales como en playlists, y tanto en modo interactivo como por CLI directa). En playlists, solicitar el formato tras definir el límite de canciones. | **RF-01**, **RF-04** |
| **`tests/test_format_validator.py`** | **Crear** | **Pruebas unitarias automatizadas**: Suite de pruebas con `pytest` para la función pura de validación/normalización de formatos en `utils/format_validator.py`. | **RF-02**, **RF-03** |

---

## 2. Funciones puras de lógica (en `utils/format_validator.py`)

Siguiendo el **Principio 3** (Lógica e interfaz separadas) y el **Principio 4** (Tests solo en módulos puros de `utils/`), no se mezcla interacción por consola con la validación de tipos:

### Constante:
```python
SUPPORTED_FORMATS: tuple[str, ...] = ("mp3", "m4a", "opus")
DEFAULT_FORMAT: str = "mp3"
```

### 1. `normalize_format_input(raw_input: Optional[str]) -> str`
- **Responsabilidad**: Limpia espacios en blanco en ambos extremos y convierte la cadena a minúsculas. Si la entrada es `None`, retorna cadena vacía `""`.
- **Parámetros**:
  - `raw_input` (`Optional[str]`): Texto ingresado por el usuario.
- **Retorno**: `str` normalizado.
- **RF Cubierto**: **RF-02**, Casos Límite 1 y 2.

### 2. `is_valid_format(formatted_text: str) -> bool`
- **Responsabilidad**: Comprueba si el texto normalizado pertenece exactamente a `SUPPORTED_FORMATS`.
- **Parámetros**:
  - `formatted_text` (`str`): Texto previamente normalizado.
- **Retorno**: `bool` (`True` si es `"mp3"`, `"m4a"` o `"opus"`; `False` en caso contrario o si supera 20 caracteres).
- **RF Cubierto**: **RF-03**, Caso Límite 3.

### 3. `resolve_audio_format(raw_input: Optional[str]) -> tuple[bool, str]`
- **Responsabilidad**: Función pura orquestadora de validación. Determina si la entrada es válida y cuál es el formato final resultante.
- **Parámetros**:
  - `raw_input` (`Optional[str]`): Entrada cruda del usuario.
- **Retorno**: `tuple[bool, str]`
  - Si es cadena vacía o espacios: `(True, "mp3")` (caso default).
  - Si es válido: `(True, format_str)`.
  - Si no es válido: `(False, "")`.
- **RF Cubierto**: **RF-02**, **RF-03**.

---

## 3. Algoritmo de elección de formato (Pseudocódigo)

### Flujo interactivo en `ui/display.py` (`prompt_audio_format`):
*(RF-01, RF-02, RF-03, Casos Límite 1, 2, 3, 4)*

```text
ALGORITMO prompt_audio_format(is_playlist: booleano) -> cadena
    SI is_playlist ES VERDADERO ENTONCES
        MOSTRAR_ADVERTENCIA("El formato seleccionado aplicará a todas las canciones de la playlist.")
    FIN SI

    intentos = 0
    max_intentos = 3

    MIENTRAS intentos < max_intentos HACER
        INTENTAR
            entrada = LEER_CONSOLA("Formato de audio [mp3/m4a/opus] (Enter = mp3): ")
        CAPTURAR KeyboardInterrupt
            REGISTRAR_LOG_INFO("Format selection interrupted by user.")
            LANZAR KeyboardInterrupt  // main captura y sale limpiamente (Caso Límite 4)
        FIN INTENTAR

        es_valido, formato_elegido = resolve_audio_format(entrada)

        SI es_valido ES VERDADERO ENTONCES
            REGISTRAR_LOG_INFO("Selected audio format: " + formato_elegido)
            RETORNAR formato_elegido
        SINO
            intentos = intentos + 1
            REGISTRAR_LOG_DEBUG("Invalid format option entered: '" + entrada + "'")
            SI intentos < max_intentos ENTONCES
                MOSTRAR_ADVERTENCIA("Opción no válida. Los formatos disponibles son: mp3, m4a, opus.")
            FIN SI
        FIN SI
    FIN MIENTRAS

    MOSTRAR_ADVERTENCIA("Se superó el límite de reintentos. Se aplicará el formato por defecto: mp3.")
    REGISTRAR_LOG_INFO("Max retries exceeded. Falling back to default format: mp3")
    RETORNAR "mp3"
FIN ALGORITMO
```

---

## 4. Diseño en la Interfaz de Usuario (Rich)

Cumpliendo el **Principio 6** (Español al usuario):

### 1. Canción individual / Modo Búsqueda / Modo CLI con argumento directo:
*(RF-01)*
```text
Descargar Audio o Playlist
Ingresa la URL o término de búsqueda: Yesterday The Beatles
ℹ Búsqueda por texto: 'Yesterday The Beatles'. Buscando el mejor resultado...

Formato de audio [mp3/m4a/opus] (Enter = mp3): _
```

### 2. Playlist:
*(RF-01)*
```text
Configuración de Playlist
¿Cuántas canciones deseas descargar? (Enter = todas): 5
⚠ El formato seleccionado aplicará a todas las canciones de la playlist.
Formato de audio [mp3/m4a/opus] (Enter = mp3): _
```

### 3. Reintentos ante entrada inválida:
*(RF-03)*
```text
Formato de audio [mp3/m4a/opus] (Enter = mp3): flac
⚠ Opción no válida. Los formatos disponibles son: mp3, m4a, opus.
Formato de audio [mp3/m4a/opus] (Enter = mp3): _
```

### 4. Agotamiento de 3 reintentos:
*(RF-03)*
```text
⚠ Se superó el límite de intentos (3). Se aplicará el formato por defecto: mp3.
```

### 5. Advertencia por degradación de metadatos o carátula:
*(RF-05)*
```text
⚠ [Metadatos]: La incrustación de carátula frontal no está disponible para formato opus. El archivo de audio se guardó intacto.
```

---

## 5. Decisiones Técnicas Justificadas y Alternativas Descartadas

### Decisión 1: Función de validación pura en `utils/format_validator.py`
- **Justificación**: Cumple el **Principio 3** (Lógica e interfaz separadas) y el **Principio 4** (Tests unitarios sin dependencias adicionales en `utils/`).
- **Alternativa descartada**: Validar directamente dentro del bucle `while` en `ui/display.py` o `main.py`. *Descartada porque mezclaría `input()` o llamadas de consola con la lógica de negocio, haciendo imposible probarla con `pytest` de manera limpia y sin mocks complejos.*

### Decisión 2: Delegación del códec al postprocesador de `yt-dlp` (`FFmpegExtractAudio`)
- **Justificación**: `yt-dlp` soporta de manera nativa `'preferredcodec': 'mp3'`, `'preferredcodec': 'm4a'` y `'preferredcodec': 'opus'` apoyándose en el binario local existente de FFmpeg (`bin/ffmpeg.exe`). No requiere librerías adicionales ni cambios en la Constitución (**Principio 1**).
- **Alternativa descartada**: Descargar primero el stream crudo `.webm` / `.mp4` y luego ejecutar subprocesos manuales de FFmpeg desde Python. *Descartada por complejidad innecesaria, riesgo de fugas de procesos zombi y romper la arquitectura probada de `downloader.py`.*

### Decisión 3: Degradación segura en `metadata/writer.py`
- **Justificación**: `mutagen` soporta tags ID3 nativos en MP3 (`EasyID3`, `ID3`, `APIC`). Para formatos como `m4a` (`MP4`) y `opus` (`OggOpus`), si la incrustación de imagen o campos particulares falla o requiere estructuras complejas, el módulo captura el evento, registra un `logger.warning(...)` en inglés y retorna `False` en `metadata_applied`, permitiendo que el archivo de audio se preserve al 100% (**RF-05**, **Principio 5**).
- **Alternativa descartada**: Levantar una excepción y eliminar el audio si la portada falla. *Descartada porque viola el RF-05 y el Principio 5 (los archivos del usuario son sagrados).*

### Decisión 4: Pregunta interactiva en ejecuciones CLI directas (`main.py <query>`)
- **Justificación**: Cumple expresamente la decisión de diseño acordada en la especificación (**RF-01**): mantener el flujo uniforme y guiado incluso cuando el usuario invoca Coda directamente desde terminal, evitando banderas adicionales y garantizando que el usuario siempre elija su formato.
- **Alternativa descartada**: Usar un flag CLI obligatorio como `-f opus`. *Descartada porque rompería la experiencia informal/guiada deseada por el usuario para esta versión.*

---

## 6. Estrategia de Tests (`pytest tests/ -v`)

En estricto apego al **Principio 4 de la Constitución** (*Las pruebas en tests/ solo cubren módulos puros (utils/). Se ejecutan con pytest tests/ -v y deben pasar al 100% antes de cualquier merge*), crearemos el archivo `tests/test_format_validator.py`.

### Casos de prueba a implementar:
1. `test_normalize_format_input_with_valid_data`:
   - `"MP3"` -> `"mp3"`
   - `"  opus  "` -> `"opus"`
   - `"M4a"` -> `"m4a"`
2. `test_normalize_format_input_with_empty_or_whitespace`:
   - `""` -> `""`
   - `"    "` -> `""`
   - `None` -> `""`
3. `test_is_valid_format_success`:
   - Evaluar `"mp3"`, `"m4a"`, `"opus"` -> todos deben dar `True`.
4. `test_is_valid_format_unsupported`:
   - `"flac"`, `"wav"`, `"aac"`, `"ogg"`, `"mp4"`, `"video"` -> todos deben dar `False`.
5. `test_is_valid_format_extreme_lengths`:
   - String de 100 caracteres -> `False`.
6. `test_resolve_audio_format_default`:
   - `""` -> `(True, "mp3")`
   - `"   "` -> `(True, "mp3")`
   - `None` -> `(True, "mp3")`
7. `test_resolve_audio_format_explicit`:
   - `"opus"` -> `(True, "opus")`
   - `" M4A "` -> `(True, "m4a")`
8. `test_resolve_audio_format_invalid`:
   - `"archivo_invalido"` -> `(False, "")`

### Comando de verificación:
```powershell
pytest tests/ -v
```
Objetivo: **100% de tests aprobados** (los 9 tests existentes de `test_validator.py` y `test_file_manager.py` + los nuevos de `test_format_validator.py`).
