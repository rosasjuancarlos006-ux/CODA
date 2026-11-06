# Plan de Implementación Técnica — Soporte Multiplataforma (002-platform)

Este documento detalla la arquitectura técnica, módulos, funciones puras, algoritmos, interfaz de usuario y estrategia de pruebas para implementar el soporte de plataformas (YouTube y YouTube Music) según lo especificado en `specs/002-platform/spec.md` y en conformidad estricta con `docs/constitution.md`.

---

## 1. Archivos a crear o modificar y sus responsabilidades

| Archivo | Estado | Responsabilidad y cambios previstos | RF Cubiertos |
| :--- | :--- | :--- | :--- |
| **`utils/platform_validator.py`** | **Crear** | **Lógica pura y desacoplada**: Definición de plataformas soportadas (`youtube`, `youtube_music`), normalización de entradas del selector colapsando espacios internos y reconociendo alias (`1`, `yt`, `music`, `ytmusic`), detección de plataforma por dominio de URL y función pura de resolución de discrepancias. Sin I/O ni interacción de consola. | **RF-01**, **RF-02**, **RF-05** |
| **`utils/validator.py`** | **Modificar** | **Clasificación pura de URLs y poda de mixes**: Extender regex para incluir `music.youtube.com`. Regla estricta: URLs con ruta `/watch` y parámetro `v=` se clasifican como `video` individual (incluso con `&list=RD...` o mixes automáticos). Añadir función pura `clean_video_url` para sanear la URL eliminando `&list=...` cuando sea track individual. Solo URLs de lista pura (`/playlist?list=...` o enlaces sin `/watch`) se clasifican como `playlist`. | **RF-03** |
| **`core/resolver.py`** | **Modificar** | **Resolución contextual por catálogo**: Añadir parámetro `platform: PlatformType = "youtube"` a `resolve_query`. Si el modo es `search`, anteponer `ytsearch1:{query}` para YouTube general, o `ytsearch1:{query} Audio Oficial` para YouTube Music (priorizando pistas y versiones de estudio oficiales sin dependencias externas). En modo video, aplicar saneamiento de URL (`clean_video_url`). | **RF-03**, **RF-04** |
| **`ui/display.py`** | **Modificar** | **Capa de presentación**: Implementar `prompt_platform() -> PlatformType` retornando identificador interno en minúsculas (`"youtube"` o `"youtube_music"`), captura limpia de `KeyboardInterrupt`, hasta 3 reintentos y fallback a `"youtube"`. Proveer helper de visualización `get_platform_display_name(platform: PlatformType) -> str` y advertencia visual `show_platform_mismatch_warning(selected: PlatformType, detected: PlatformType)` en español. | **RF-01**, **RF-05**, **RF-06** |
| **`main.py`** | **Modificar** | **Orquestación del flujo lineal**: En modo interactivo, ejecutar estrictamente: 1. Plataforma ➔ 2. Consulta ➔ Auto-adaptación con advertencia visual si aplica ➔ 3. Límite de canciones (si es playlist) ➔ 4. Formato de audio (`prompt_audio_format`) ➔ 5. Descarga. En ejecuciones directas por CLI (`args.query`), inferir automáticamente la plataforma del enlace o asignar YouTube en texto libre sin preguntas redundantes. | **RF-01**, **RF-02**, **RF-05**, **RF-06** |
| **`tests/test_platform_validator.py`** | **Crear** | **Pruebas unitarias automatizadas**: Pruebas con `pytest` para la normalización de alias, colapso de espacios, detección de dominios por URL y detección de discrepancias. | **RF-01**, **RF-02**, **RF-05** |
| **`tests/test_validator.py`** | **Modificar** | **Pruebas unitarias de URLs y saneamiento**: Casos para `music.youtube.com`, playlists musicales, prioridad de video individual y función pura `clean_video_url`. | **RF-03** |

---

## 2. Funciones puras de lógica (Módulos en `utils/`)

Siguiendo el **Principio 3** (Lógica e interfaz separadas) y el **Principio 4** (Tests solo en módulos puros de `utils/`):

### En `utils/platform_validator.py`:

```python
from typing import Optional, Tuple, Literal

PlatformType = Literal["youtube", "youtube_music"]

SUPPORTED_PLATFORMS: Tuple[PlatformType, ...] = ("youtube", "youtube_music")
DEFAULT_PLATFORM: PlatformType = "youtube"

PLATFORM_DISPLAY_NAMES = {
    "youtube": "YouTube",
    "youtube_music": "YouTube Music"
}
```

#### 1. `normalize_platform_input(raw_input: Optional[str]) -> Tuple[bool, Optional[PlatformType]]`
- **Responsabilidad**: Limpia espacios a los extremos, colapsa espacios internos múltiples a uno solo (`"youtube   music"` -> `"youtube music"`) y convierte a minúsculas. Valida contra los alias aceptados.
- **Parámetros**:
  - `raw_input` (`Optional[str]`): Entrada de consola del usuario.
- **Retorno**:
  - Si es vacío, solo espacios o `None`: `(True, "youtube")` (default).
  - Si coincide con alias de YouTube (`"1"`, `"youtube"`, `"yt"`): `(True, "youtube")`.
  - Si coincide con alias de YouTube Music (`"2"`, `"youtube music"`, `"music"`, `"ytmusic"`, `"yt_music"`): `(True, "youtube_music")`.
  - Cualquier otro valor inválido: `(False, None)`.
- **RF Cubierto**: **RF-01**, Casos Límite 3 y 5.

#### 2. `detect_url_platform(url: str) -> Optional[PlatformType]`
- **Responsabilidad**: Analiza el dominio de una URL y retorna a qué plataforma pertenece, o `None` si es texto de búsqueda o una URL ajena a los dominios soportados.
- **Parámetros**:
  - `url` (`str`): Cadena con enlace o texto.
- **Retorno**:
  - `"youtube_music"` si contiene `music.youtube.com`.
  - `"youtube"` si coincide con `youtube.com` o `youtu.be` (y no es `music.youtube.com`).
  - `None` si es texto libre o URL externa (ej. `spotify.com`).
- **RF Cubierto**: **RF-02**, **RF-05**.

#### 3. `check_platform_mismatch(selected_platform: PlatformType, url: str) -> Tuple[bool, PlatformType]`
- **Responsabilidad**: Función pura que determina si hay discrepancia entre la plataforma elegida y el enlace suministrado.
- **Parámetros**:
  - `selected_platform` (`PlatformType`): Plataforma activa elegida por el usuario.
  - `url` (`str`): URL ingresada por el usuario.
- **Retorno**:
  - `(True, detected_platform)` si el enlace pertenece a la otra plataforma (se debe auto-adaptar).
  - `(False, selected_platform)` si no hay discrepancia o si la entrada es texto libre / URL no clasificada.
- **RF Cubierto**: **RF-05**.

### En `utils/validator.py`:

#### 4. `clean_video_url(url: str) -> str`
- **Responsabilidad**: Si la URL es de video (`/watch?v=ID`), poda los parámetros de listas, radios o seguimiento (`&list=...`, `&index=...`, `&feature=...`), dejando una URL limpia para evitar que `yt-dlp` procese listas infinitas accidentales.
- **Parámetros**:
  - `url` (`str`): URL de video.
- **Retorno**:
  - `str` de URL limpia o la misma URL si no es de video.
- **RF Cubierto**: **RF-03**, Caso Límite 2.

#### 5. `is_playlist_url(text: str) -> bool` y `classify_input(text: str) -> InputType` (Actualizadas)
- **Responsabilidad**:
  - Reconocer dominios `music.youtube.com` y `www.music.youtube.com`.
  - Si contiene `/watch` con parámetro `v=`, se clasifica como `video` (prioridad de track individual).
  - Se clasifica como `playlist` solo si es ruta pura de playlist (`/playlist?list=...`) o no contiene parámetro de video individual.
- **RF Cubierto**: **RF-03**, Casos Límite 1 y 2.

---

## 3. Algoritmo del flujo de trabajo (Pseudocódigo)

### Flujo interactivo en `main.py` (`handle_download_prompt`):
*(RF-01, RF-04, RF-05, RF-06)*

```text
ALGORITMO handle_download_prompt(output_dir)
    // PASO 1: Selección de plataforma
    INTENTAR
        plataforma = prompt_platform()  // Retorna "youtube" o "youtube_music"
    CAPTURAR KeyboardInterrupt
        REGISTRAR_LOG_INFO("Platform selection cancelled by user.")
        MOSTRAR_ADVERTENCIA("Operación cancelada por el usuario.")
        RETORNAR
    FIN INTENTAR

    REGISTRAR_LOG_INFO("Selected platform: " + plataforma)
    nombre_plataforma = get_platform_display_name(plataforma)  // "YouTube" o "YouTube Music"

    // PASO 2: Entrada de consulta
    MOSTRAR_MENSAJE("Descargar desde " + nombre_plataforma)
    entrada_usuario = LEER_CONSOLA("Ingresa la URL o término de búsqueda: ")
    SI entrada_usuario ESTA VACIA ENTONCES
        MOSTRAR_ADVERTENCIA("No ingresaste ningún texto o enlace.")
        RETORNAR
    FIN SI

    // Detección de discrepancia y auto-adaptación pedagógica
    hay_discrepancia, plataforma_adaptada = check_platform_mismatch(plataforma, entrada_usuario)
    SI hay_discrepancia ES VERDADERO ENTONCES
        nombre_detectada = get_platform_display_name(plataforma_adaptada)
        nombre_original = get_platform_display_name(plataforma)
        MOSTRAR_ADVERTENCIA("Aviso: Habías seleccionado " + nombre_original + ", pero el enlace pertenece a " + nombre_detectada + ".")
        MOSTRAR_INFO("Se adaptará automáticamente la descarga para procesar el contenido de " + nombre_detectada + ".")
        REGISTRAR_LOG_WARNING("Platform mismatch detected: URL belongs to " + plataforma_adaptada + ". Auto-adapting.")
        plataforma = plataforma_adaptada
    FIN SI

    // Resolver consulta según catálogo (con poda de &list= si es video individual)
    resuelto = resolve_query(entrada_usuario, platform=plataforma)
    modo = resuelto["mode"]      // 'video', 'playlist' o 'search'
    query = resuelto["query"]

    // PASO 3: Límite de canciones si es playlist
    limite = 0
    SI modo == "playlist" ENTONCES
        limite = consultar_limite_playlist()
    FIN SI

    // PASO 4: Selección de formato de audio
    es_playlist = (modo == "playlist")
    formato_audio = prompt_audio_format(is_playlist=es_playlist)

    // PASO 5: Descarga y conversión
    SI modo == "playlist" ENTONCES
        ejecutar_descarga_playlist(query, output_dir, limite, formato_audio)
    SINO
        ejecutar_descarga_individual(query, output_dir, formato_audio)
    FIN SI
FIN ALGORITMO
```

### Flujo directo por CLI en `main.py` (`main()`):
*(RF-02)*

```text
ALGORITMO ejecutar_cli_directo(query_arg, output_dir, limite_arg)
    // Inferencia automática sin preguntas redundantes
    plataforma_detectada = detect_url_platform(query_arg)
    SI plataforma_detectada NO ES NULO ENTONCES
        plataforma = plataforma_detectada
    SINO
        plataforma = "youtube"  // Texto libre o enlace estándar
    FIN SI
    REGISTRAR_LOG_INFO("CLI direct execution inferred platform: " + plataforma)

    resuelto = resolve_query(query_arg, platform=plataforma)
    modo = resuelto["mode"]
    query = resuelto["query"]

    SI modo == "playlist" ENTONCES
        formato = prompt_audio_format(is_playlist=True)
        ejecutar_descarga_playlist(query, output_dir, limite_arg, formato)
    SINO
        formato = prompt_audio_format(is_playlist=False)
        ejecutar_descarga_individual(query, output_dir, formato)
    FIN SI
FIN ALGORITMO
```

---

## 4. Diseño en la Interfaz de Usuario (Rich)

Cumpliendo el **Principio 6** (Español al usuario):

### 1. Selector interactivo de plataforma:
*(RF-01, RF-06)*
```text
Plataforma de Descarga
  [1] YouTube (Catálogo general, videos, directos)
  [2] YouTube Music (Pistas oficiales, álbumes, música de estudio)

Selecciona una plataforma [1/2] (Enter = YouTube): _
```

### 2. Advertencia ante entrada inválida y reintento:
*(RF-01)*
```text
Selecciona una plataforma [1/2] (Enter = YouTube): spotify
⚠ Opción no válida. Ingresa 1 (YouTube) o 2 (YouTube Music).
Selecciona una plataforma [1/2] (Enter = YouTube): _
```

### 3. Agotamiento de 3 reintentos:
*(RF-01)*
```text
⚠ Se superó el límite de reintentos. Se seleccionará YouTube por defecto.
```

### 4. Advertencia de auto-adaptación por enlace cruzado:
*(RF-05)*
```text
Ingresa la URL o término de búsqueda: https://music.youtube.com/watch?v=dQw4w9WgXcQ
⚠ Aviso: Habías seleccionado YouTube general, pero el enlace pertenece a YouTube Music.
ℹ Se adaptará automáticamente la descarga para procesar el contenido de YouTube Music.
```

### 5. Búsqueda orientada por catálogo musical:
*(RF-04)*
```text
ℹ Búsqueda en YouTube Music: 'Coldplay Yellow'. Buscando la pista oficial...
```

---

## 5. Decisiones Técnicas Justificadas y Alternativas Descartadas

### Decisión 1: Módulo puro `utils/platform_validator.py`
- **Justificación**: Aisla las reglas de validación y alias de la presentación en pantalla. Cumple estrictamente el **Principio 3** (Lógica e interfaz separadas) y el **Principio 4** (Tests unitarios sin dependencias externas).
- **Alternativa descartada**: Manejar las comparaciones de texto directamente dentro de `main.py` o `ui/display.py`. *Descartada porque viola la separación de responsabilidades y dificulta la cobertura de pruebas.*

### Decisión 2: Poda de `&list=` en enlaces mixtos vía `clean_video_url`
- **Justificación**: Garantiza de forma determinista que enlaces tipo `watch?v=ID&list=RD...` solo descarguen la pista individual deseada, evitando que `yt-dlp` descargue listas automáticas infinitas (**RF-03**).
- **Alternativa descartada**: Dejar la URL intacta confiando solo en `noplaylist: True`. *Descartada porque ciertas versiones de yt-dlp pueden generar advertencias o comportamientos imprevistos al resolver extractors de playlist en URLs con mix.*

### Decisión 3: Enriquecimiento contextual para búsquedas en YouTube Music
- **Justificación**: Añadir `"Audio Oficial"` al query de búsqueda (`ytsearch1:{query} Audio Oficial`) permite priorizar versiones de estudio y temas de catálogo oficial de YouTube Music sin violar el **Principio 1** (Stack mínimo: sin APIs ni dependencias extras).
- **Alternativa descartada**: Instalar una librería externa de scraping específica de YouTube Music. *Descartada porque violaría la Constitución y aumentaría la fragilidad ante cambios de YouTube.*

### Decisión 4: Retorno técnico interno (`PlatformType`) y helper para nombres en español
- **Justificación**: Cumple el **Principio 6** (Español al usuario, inglés al código). El código maneja constantes tipadas `"youtube"` / `"youtube_music"`, los logs registran en inglés y la UI traduce a `"YouTube"` / `"YouTube Music"`.
- **Alternativa descartada**: Usar cadenas en español en todo el código interno. *Descartada por romper las convenciones de tipado estricto e inglés en la arquitectura interna.*

---

## 6. Estrategia de Tests (`pytest tests/ -v`)

Siguiendo el **Principio 4 de la Constitución** (*Las pruebas en tests/ solo cubren módulos puros (utils/). Se ejecutan con pytest tests/ -v y deben pasar al 100% antes de cualquier merge*):

### Tests a crear en `tests/test_platform_validator.py`:
1. `test_normalize_platform_default`:
   - `""` -> `(True, "youtube")`
   - `"   "` -> `(True, "youtube")`
   - `None` -> `(True, "youtube")`
2. `test_normalize_platform_youtube_aliases`:
   - `"1"`, `"youtube"`, `"YT"`, `" YouTube "` -> `(True, "youtube")`
3. `test_normalize_platform_youtube_music_aliases`:
   - `"2"`, `"music"`, `"ytmusic"`, `"YouTube Music"`, `"youtube   music"` (espacios colapsados) -> `(True, "youtube_music")`
4. `test_normalize_platform_invalid`:
   - `"spotify"`, `"3"`, `"apple"` -> `(False, None)`
5. `test_detect_url_platform`:
   - `"https://music.youtube.com/watch?v=123"` -> `"youtube_music"`
   - `"https://www.music.youtube.com/playlist?list=PL1"` -> `"youtube_music"`
   - `"https://www.youtube.com/watch?v=123"` -> `"youtube"`
   - `"https://youtu.be/123"` -> `"youtube"`
   - `"cancion sin url"` -> `None`
6. `test_check_platform_mismatch`:
   - Elegido `youtube`, URL `music.youtube.com` -> `(True, "youtube_music")`
   - Elegido `youtube_music`, URL `youtube.com` -> `(True, "youtube")`
   - Elegido `youtube`, URL `youtube.com` -> `(False, "youtube")`
   - Elegido `youtube_music`, texto libre -> `(False, "youtube_music")`

### Tests a extender en `tests/test_validator.py`:
7. `test_youtube_music_urls`:
   - Validar que `is_valid_youtube_url` retorne `True` para `https://music.youtube.com/watch?v=ABC`.
8. `test_youtube_music_playlist_urls`:
   - `https://music.youtube.com/playlist?list=PL123` -> `is_playlist_url` es `True`.
9. `test_mix_url_priority_as_single_track`:
   - `https://music.youtube.com/watch?v=ABC&list=RDABC` -> `classify_input` retorna `"video"`.
10. `test_clean_video_url`:
    - `"https://music.youtube.com/watch?v=ABC&list=RDABC&index=1"` -> `"https://music.youtube.com/watch?v=ABC"`
    - `"https://www.youtube.com/watch?v=ABC&feature=share"` -> `"https://www.youtube.com/watch?v=ABC"`

### Comando de verificación:
```powershell
pytest tests/ -v
```
Objetivo: **100% de tests aprobados** (los 18 tests existentes + los nuevos tests de plataforma).
