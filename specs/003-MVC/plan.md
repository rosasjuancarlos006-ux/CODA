# Plan de Implementación Técnica — Arquitectura Modelo-Vista-Controlador (003-MVC)

Este documento detalla el diseño técnico, la redistribución modular de responsabilidades, las funciones puras de lógica, los algoritmos en pseudocódigo, la representación visual, las decisiones de ingeniería justificadas y la estrategia integral de pruebas para la refactorización a la arquitectura **Modelo-Vista-Controlador (MVC)** de Coda, conforme a `specs/003-MVC/spec.md` y a los principios de `docs/constitution.md`.

---

## 1. Archivos a crear o modificar y sus responsabilidades

| Archivo | Estado | Responsabilidad y cambios previstos | RF Cubiertos |
| :--- | :--- | :--- | :--- |
| **`docs/constitution.md`** | **Modificar** | **Gobernanza del proyecto**: Enmendar formalmente la **Regla 4** para permitir pruebas unitarias del controlador y de contratos mediante vistas simuladas (*mocks*/*fakes* en memoria con la biblioteca estándar), sin añadir dependencias de prueba externas. | **Criterio Finalización 1**, **RNF-01** |
| **`AGENTS.md`** | **Modificar** | **Documentación de arquitectura**: Actualizar la estructura de directorios (`controllers/`, `ui/`, `core/`), mapa de responsabilidades y convenciones de testing para reflejar el patrón MVC antes de finalizar. | **Criterio Finalización 2** |
| **`core/events.py`** | **Crear** | **Modelo de eventos desacoplado**: Definición agnóstica de `DownloadPhase` (Enum con fases: `PREPARING`, `DOWNLOADING`, `CONVERTING`, `METADATA`, `COMPLETED`, `ERROR`), `ProgressEvent` (dataclass con métricas neutras: fase, porcentaje, velocidad, tiempo estimado, índice actual, total) y `DownloadResult` (resultado estructurado). Sin imports de UI. | **RF-01**, **RF-05**, **RNF-02** |
| **`ui/view_interface.py`** | **Crear** | **Contrato abstracto de presentación**: Interfaz pura (`typing.Protocol`) que estipula todas las interacciones de entrada/salida: solicitud de plataforma, consulta, formato, límite, visualización de menú, advertencias, errores, tablas y actualización de progreso por eventos. | **RF-01**, **RF-05**, **RF-06**, **RNF-02** |
| **`ui/terminal_view.py`** | **Crear** | **Implementación concreta de Vista en Terminal**: Implementa `ViewInterface` consumiendo `rich` (paneles, tablas, barras de progreso y spinners). Renderiza eventos de progreso con degradación visual cuando no hay métricas numéricas. Centraliza el formateo en español. | **RF-01**, **RF-05**, **RF-06**, **RF-07**, **RNF-04** |
| **`ui/display.py`** | **Modificar** | **Adaptador / compatibilidad legacy**: Redirige sus llamadas a `TerminalView` o conserva utilidades estéticas compartidas para garantizar cero regresión en módulos existentes durante la transición. | **RF-01**, **RNF-04** |
| **`controllers/download_controller.py`** | **Crear** | **Coordinador central (Controlador)**: Orquesta el flujo de interacción interactivo y la ejecución CLI directa. Aplica la taxonomía de errores (recuperables vs. fatales), gestiona cancelaciones (`KeyboardInterrupt`), coordina la limpieza de archivos parciales y delega el renderizado a la vista inyectada (`ViewInterface`). | **RF-01**, **RF-02**, **RF-03**, **RF-04**, **RF-05**, **RF-07** |
| **`utils/file_manager.py`** | **Modificar** | **Lógica pura de archivos**: Añadir funciones puras para escanear y listar metadatos de archivos de audio soportados (`.mp3`, `.m4a`, `.opus`), y función pura de resolución de archivos temporales/huérfanos a limpiar tras cancelación. | **RF-03**, **RF-06**, **RNF-03** |
| **`core/downloader.py`** | **Modificar** | **Motor de descarga (Modelo)**: Adaptar los callbacks de `yt-dlp` para emitir instancias de `ProgressEvent`. Implementar captura de cancelación que marque archivos temporales para supuración. Desacoplado al 100% de la consola Rich. | **RF-03**, **RF-05**, **RNF-02**, **RNF-03** |
| **`main.py`** | **Modificar** | **Punto de arranque (Bootstrap)**: Inicializador mínimo (< 35 líneas). Parsea argumentos CLI, resuelve el directorio de salida, instancia `TerminalView()`, ensambla `DownloadController(view=view, output_dir=output_dir)` y ejecuta `controller.run(args)`. | **RF-01**, **RF-04** |
| **`tests/test_controller.py`** | **Crear** | **Pruebas unitarias de orquestación**: Tests con `FakeView` en memoria verificando el flujo interactivo, recuperación ante entradas erróneas, retorno al menú ante fallos de red, código de salida en modo CLI y respuesta a `KeyboardInterrupt`. | **RF-01**, **RF-02**, **RF-03**, **RF-04** |
| **`tests/test_events.py`** | **Crear** | **Pruebas unitarias de modelos de eventos**: Validación de instanciación, inmutabilidad y cálculo de degradación de `ProgressEvent`. | **RF-05** |
| **`tests/test_file_manager.py`** | **Modificar** | **Pruebas de gestión de archivos**: Pruebas para filtrado de extensiones válidas de audio y detección de archivos temporales huérfanos. | **RF-03**, **RF-06** |

---

## 2. Funciones puras de lógica (Módulos de Dominio y Utilidades)

En estricta observancia del **Principio 3** (Lógica e interfaz separadas) y el **Principio 4** (Tests unitarios sin dependencias externas):

### En `core/events.py`:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DownloadPhase(Enum):
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    METADATA = "metadata"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass(frozen=True)
class ProgressEvent:
    phase: DownloadPhase
    percentage: Optional[float] = None
    speed_bytes_sec: Optional[float] = None
    eta_seconds: Optional[int] = None
    current_item: Optional[int] = None
    total_items: Optional[int] = None
    item_title: Optional[str] = None
    message: Optional[str] = None
```

#### 1. `create_progress_event(...) -> ProgressEvent`
- **Responsabilidad**: Función pura que construye y valida un evento de progreso a partir de diccionarios crudos de `yt-dlp` o transiciones de fase internas.
- **Parámetros**:
  - `phase` (`DownloadPhase`): Fase actual del proceso.
  - `percentage` (`Optional[float]`): Progreso normalizado de 0.0 a 100.0 (o `None` si es indeterminado).
  - `speed` (`Optional[float]`): Velocidad en bytes/segundo.
  - `eta` (`Optional[int]`): Segundos restantes estimados.
  - `current_item` (`Optional[int]`): Índice de pista actual en playlists.
  - `total_items` (`Optional[int]`): Total de canciones en la colección.
  - `title` (`Optional[str]`): Título de la pista en curso.
- **Retorno**: Instancia inmutable `ProgressEvent`.
- **RF Cubierto**: **RF-05**.

---

### En `utils/file_manager.py`:

```python
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set

SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {".mp3", ".m4a", ".opus"}

@dataclass(frozen=True)
class AudioFileInfo:
    name: str
    path: Path
    format: str
    size_bytes: int
    modified_timestamp: float
```

#### 2. `scan_audio_downloads(directory: Path) -> List[AudioFileInfo]`
- **Responsabilidad**: Escanea un directorio y retorna exclusivamente metadatos de los archivos cuyas extensiones pertenezcan a `SUPPORTED_AUDIO_EXTENSIONS`, ordenados de forma descendente por fecha de modificación. No produce salidas por pantalla.
- **Parámetros**:
  - `directory` (`Path`): Carpeta donde se almacenan las descargas.
- **Retorno**: `List[AudioFileInfo]` (vacía si no hay coincidencias o si el directorio no existe).
- **RF Cubierto**: **RF-06**, Caso Límite 7.

#### 3. `find_partial_download_files(output_dir: Path, download_start_timestamp: float) -> List[Path]`
- **Responsabilidad**: Identifica archivos temporales o incompletos generados a partir de una marca de tiempo dada (archivos `.part`, `.ytdl`, `.temp`, o archivos de audio modificados con posterioridad al inicio que no finalizaron su proceso).
- **Parámetros**:
  - `output_dir` (`Path`): Directorio de descargas.
  - `download_start_timestamp` (`float`): Marca de tiempo epoch en que inició la operación cancelada.
- **Retorno**: `List[Path]` con los archivos huérfanos candidatos a eliminación.
- **RF Cubierto**: **RF-03**, Casos Límite 1 y 6.

#### 4. `cleanup_files(file_paths: List[Path]) -> int`
- **Responsabilidad**: Elimina de forma segura la lista de rutas recibidas, capturando excepciones de sistema de archivos sin propagar fallos.
- **Parámetros**:
  - `file_paths` (`List[Path]`): Rutas a suprimir.
- **Retorno**: Cantidad de archivos eliminados exitosamente.
- **RF Cubierto**: **RF-03**, **RNF-03**.

---

### En `ui/view_interface.py`:

```python
from typing import Protocol, Optional, List, Dict, Any
from pathlib import Path
from core.events import ProgressEvent
from utils.file_manager import AudioFileInfo

class ViewInterface(Protocol):
    def show_banner(self) -> None: ...
    def show_main_menu(self) -> str: ...
    def prompt_platform(self) -> str: ...
    def prompt_query(self, platform_name: str) -> str: ...
    def prompt_playlist_limit(self) -> Optional[int]: ...
    def prompt_audio_format(self, is_playlist: bool) -> str: ...
    def show_platform_mismatch(self, selected: str, adapted: str) -> None: ...
    def show_info(self, message: str) -> None: ...
    def show_warning(self, message: str) -> None: ...
    def show_error(self, message: str, error_type: Optional[str] = None) -> None: ...
    def show_single_success(self, result: Dict[str, Any]) -> None: ...
    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None: ...
    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None: ...
    def show_empty_downloads(self) -> None: ...
    def on_progress(self, event: ProgressEvent) -> None: ...
    def start_progress_task(self, title: str, total: Optional[int] = None) -> None: ...
    def stop_progress_task(self) -> None: ...
```
- **RF Cubierto**: **RF-01**, **RF-05**, **RF-06**, **RNF-02**.

---

## 3. Algoritmo de la arquitectura en pseudocódigo

### A. Punto de Entrada (`main.py` — Bootstrap)
*(RF-01, RF-04)*

```text
ALGORITMO main()
    INICIALIZAR logger global
    args = parse_arguments()  // Parseo de argumentos CLI
    output_dir = resolver_ruta_descargas(args.output)
    asegurar_directorio_existe(output_dir)

    // Inyección de dependencias (MVC)
    vista = TerminalView()
    controlador = DownloadController(view=vista, output_dir=output_dir)

    SI args.query ESTÁ PRESENTE ENTONCES
        codigo_salida = controlador.run_cli_direct(
            query=args.query,
            requested_format=args.format,
            playlist_limit=args.limit
        )
        sys.exit(codigo_salida)
    SINO
        controlador.run_interactive_loop()
    FIN SI
FIN ALGORITMO
```

---

### B. Bucle Interactivo Resiliente (`DownloadController.run_interactive_loop`)
*(RF-01, RF-02, RF-03, RF-06, RF-07)*

```text
ALGORITMO run_interactive_loop()
    vista.show_banner()
    
    MIENTRAS verdadero HACER
        INTENTAR
            opcion = vista.show_main_menu()
            
            CASO opcion SEA
                "1":
                    handle_interactive_download()
                "2":
                    handle_view_downloads()
                "3":
                    vista.show_info("¡Gracias por usar Coda! Hasta la próxima.")
                    RETORNAR
                OTRO:
                    vista.show_warning("Opción no válida. Por favor ingresa 1, 2 o 3.")
            FIN CASO
            
        ATRAPAR KeyboardInterrupt ENTONCES
            vista.show_warning("Interrupción detectada en el menú. Saliendo de Coda...")
            RETORNAR
        ATRAPAR Exception COMO e ENTONCES
            logger.exception("Fallo no controlado en bucle interactivo")
            vista.show_error(f"Ocurrió un error inesperado: {e}")
            // Mantiene el bucle activo sin romper la sesión (RF-02)
        FIN INTENTAR
    FIN MIENTRAS
FIN ALGORITMO
```

---

### C. Flujo Interactivo de Descarga (`DownloadController.handle_interactive_download`)
*(RF-02, RF-03, RF-05, RF-07)*

```text
ALGORITMO handle_interactive_download()
    marca_tiempo_inicio = obtener_tiempo_actual()
    
    INTENTAR
        // PASO 1: Plataforma (RF-07)
        plataforma = vista.prompt_platform() // Valida alias o default "youtube"
        
        // PASO 2: Entrada del usuario con reintento contextual ante vacío (RF-02, RF-07)
        entrada_valida = FALSO
        MIENTRAS NO entrada_valida HACER
            raw_input = vista.prompt_query(obtener_nombre_plataforma(plataforma))
            SI raw_input ESTÁ VACÍO ENTONCES
                vista.show_warning("No ingresaste ningún texto. (Escribe 'cancelar' para volver)")
            SINO SI raw_input.lower() == "cancelar" ENTONCES
                RETORNAR // Escape limpio al menú
            SINO
                user_input = raw_input
                entrada_valida = VERDADERO
            FIN SI
        FIN MIENTRAS

        // Auto-adaptación pedagógica (RF-07)
        hay_discrepancia, plataforma_adaptada = check_platform_mismatch(plataforma, user_input)
        SI hay_discrepancia ENTONCES
            vista.show_platform_mismatch(plataforma, plataforma_adaptada)
            plataforma = plataforma_adaptada
        FIN SI

        resolucion = resolve_query(user_input, platform=plataforma)
        modo = resolucion["mode"]
        query_final = resolucion["query"]

        // PASO 3: Límite si es playlist (RF-07)
        limite = NULO
        SI modo == "playlist" ENTONCES
            limite = vista.prompt_playlist_limit()
        FIN SI

        // PASO 4: Formato de audio (RF-07)
        formato = vista.prompt_audio_format(is_playlist=(modo == "playlist"))

        // PASO 5: Ejecución con progreso granular (RF-05)
        SI modo == "playlist" ENTONCES
            ejecutar_descarga_playlist(query_final, limite, formato, marca_tiempo_inicio)
        SINO
            ejecutar_descarga_individual(query_final, formato, marca_tiempo_inicio)
        FIN SI

    ATRAPAR KeyboardInterrupt ENTONCES
        // RF-03: Cancelación del usuario en interactivo
        vista.show_warning("Descarga cancelada por el usuario. Limpiando archivos parciales...")
        archivos_basura = find_partial_download_files(output_dir, marca_tiempo_inicio)
        cleanup_files(archivos_basura)
        vista.show_info("Retornando al menú principal.")
        // Regresa limpiamente al menú sin salir del programa (RF-03)
        
    ATRAPAR FFmpegMissingException ENTONCES
        // RF-02: Error de entorno fatal
        vista.show_error("FFmpeg no está disponible. Es indispensable para convertir el audio.", "ffmpeg_missing")
        vista.show_info("Instala FFmpeg en bin/ o en el PATH y vuelve a intentarlo.")
        
    ATRAPAR NetworkTimeoutException COMO e ENTONCES
        // RF-02: Error de red recuperable
        vista.show_error(f"Fallo de conexión durante la descarga: {e}", "network_timeout")
        vista.show_info("Verifica tu acceso a internet y vuelve a intentarlo.")
    FIN INTENTAR
FIN ALGORITMO
```

---

### D. Ejecución Directa CLI (`DownloadController.run_cli_direct`)
*(RF-03, RF-04)*

```text
ALGORITMO run_cli_direct(query, requested_format, playlist_limit)
    marca_tiempo_inicio = obtener_tiempo_actual()
    vista.show_banner()
    
    INTENTAR
        // Inferencia automática de plataforma sin prompts
        plataforma = detect_url_platform(query) O POR_DEFECTO "youtube"
        resolucion = resolve_query(query, platform=plataforma)
        modo = resolucion["mode"]
        query_final = resolucion["query"]
        formato = requested_format O POR_DEFECTO "mp3"
        
        SI modo == "playlist" ENTONCES
            resultado = download_playlist_core(
                query_final,
                output_dir,
                limit=playlist_limit,
                format=formato,
                on_progress=vista.on_progress
            )
            SI NO resultado["success"] ENTONCES
                vista.show_error(resultado["message"], resultado.get("error"))
                RETORNAR 1
            FIN SI
            vista.show_playlist_summary(resultado, output_dir)
        SINO
            resultado = download_single_core(
                query_final,
                output_dir,
                format=formato,
                on_progress=vista.on_progress
            )
            SI NO resultado["success"] ENTONCES
                vista.show_error(resultado["message"], resultado.get("error"))
                RETORNAR 1
            FIN SI
            vista.show_single_success(resultado)
        FIN SI
        
        RETORNAR 0 // Éxito limpio (RF-04)

    ATRAPAR KeyboardInterrupt ENTONCES
        vista.show_warning("Operación directa interrumpida por el usuario.")
        archivos_basura = find_partial_download_files(output_dir, marca_tiempo_inicio)
        cleanup_files(archivos_basura)
        RETORNAR 130 // Salida estándar de terminación por SIGINT (RF-04)

    ATRAPAR Exception COMO e ENTONCES
        vista.show_error(f"Fallo en ejecución directa: {e}")
        archivos_basura = find_partial_download_files(output_dir, marca_tiempo_inicio)
        cleanup_files(archivos_basura)
        RETORNAR 1 // Error directo sin prompts interactivos (RF-04)
    FIN INTENTAR
FIN ALGORITMO
```

---

## 4. Representación en la interfaz de usuario (`TerminalView`)

`TerminalView` implementa el contrato `ViewInterface` apoyándose en `rich`:

### Componentes visuales y mapeo de eventos:

1. **Menú y navegación (`show_main_menu`, `show_banner`)**:
   - Muestra el banner ASCII en color `bold cyan`.
   - Renderiza un `Panel` estilizado con bordes redondeados conteniendo las 3 opciones principales.
   - Solicita la opción mediante `console.input("[bold yellow]Selecciona una opción (1-3): [/bold yellow]")`.

2. **Captura y validación de prompts (`prompt_platform`, `prompt_query`, `prompt_audio_format`)**:
   - `prompt_platform`: Presenta opciones destacando `[1] YouTube (por defecto)` y `[2] YouTube Music`. Tolera alias con hasta 3 reintentos.
   - `prompt_audio_format`: Despliega `[mp3, m4a, opus] (Enter = mp3)`. Advierte unificación en caso de playlists.
   - `show_platform_mismatch`: Renderiza un panel `bold yellow` indicando la auto-adaptación pedagógica sin detener la ejecución.

3. **Renderizado de eventos de progreso y degradación visual (`on_progress`)** *(RF-05)*:
   - Utiliza una instancia administrada de `rich.progress.Progress` configurada con columnas:
     - `SpinnerColumn(spinner_name="dots")`
     - `TextColumn("[bold cyan]{task.description}")`
     - `BarColumn(bar_width=None)` (cuando hay porcentaje)
     - `TextColumn("[progress.percentage]{task.percentage:>3.0f}%")`
     - `TimeElapsedColumn()`
   - **Lógica de degradación visual**:
     - **Fase `PREPARING`**: Muestra spinner con texto `"Consultando metadatos del recurso..."`.
     - **Fase `DOWNLOADING` con métricas**: Barra de progreso activa con porcentaje, velocidad calculada (ej. `2.4 MB/s`) y tiempo estimado.
     - **Fase `DOWNLOADING` sin métricas (stream dinámico)**: La barra se oculta o se marca como pulsante continua (indeterminada), mostrando spinner y bytes transferidos.
     - **Fase `CONVERTING`**: Actualiza la descripción a `"[bold cyan]Convirtiendo audio a {formato.upper()} vía FFmpeg..."` con spinner activo y barra detenida.
     - **Fase `METADATA`**: Actualiza a `"[bold magenta]Incrustando etiquetas ID3 y carátula oficial..."`.
     - **Playlists**: Se agrega columna `MofNCompleteColumn()` mostrando el avance `Canción X de Y: {título}`.

4. **Visualización de descargas (`show_downloads_table`, `show_empty_downloads`)** *(RF-06)*:
   - Si la lista `downloads` está vacía, `show_empty_downloads` imprime un panel amigable:
     `[dim cyan]No se encontraron archivos de audio descargados en la carpeta de salida.[/dim cyan]`.
   - Si contiene archivos, `show_downloads_table` genera una `Table(title="🎵 Canciones Descargadas")` con columnas:
     - *Archivo* (`bold white`)
     - *Formato* (`bold green`)
     - *Tamaño* (`yellow`, formateado a KB/MB legibles)
     - *Fecha* (`dim white`, formateada `YYYY-MM-DD HH:MM`).

---

## 5. Decisiones técnicas justificadas y alternativas descartadas

### Decisión 1: Uso de `typing.Protocol` para `ViewInterface`
- **Elección**: Definir `ViewInterface` como un `Protocol` de Python (subtipado estructural / duck typing estático).
- **Justificación**: Permite que cualquier clase (ej. `TerminalView`, una futura `FletView` o un `FakeView` en pruebas) satisfaga el contrato sin necesidad de heredar obligatoriamente de una clase base común, facilitando el mocking instantáneo en tests unitarios.
- **Alternativa descartada**: `abc.ABC` con herencia obligatoria. Descartada porque acopla la jerarquía de clases e impone una sobrecarga innecesaria en vistas alternativas o envoltorios ligeros de pruebas.

### Decisión 2: Desacoplamiento de eventos mediante `dataclass` neutra (`ProgressEvent`)
- **Elección**: Crear un DTO inmutable `ProgressEvent` en `core/events.py` que transporta tipos primitivos (`float`, `int`, `str`, `Enum`).
- **Justificación**: El Modelo (`core/downloader.py`) únicamente emite este evento a través de un callback genérico `Callable[[ProgressEvent], None]`. El Modelo jamás importa Rich ni sabe si el consumidor es una terminal, una consola plana o una ventana gráfica.
- **Alternativa descartada**: Pasar la instancia `Progress` o `Console` de Rich directamente al downloader. Descartada de raíz por violar el **Principio 3** de la Constitución y hacer imposible el cambio a Flet.

### Decisión 3: Enmienda formal a la Regla 4 de la Constitución
- **Elección**: Modificar la Regla 4 en `docs/constitution.md` para redactarla así:
  *"Las pruebas en `tests/` cubren módulos puros (`utils/`) y la lógica de coordinación del controlador utilizando vistas simuladas en memoria (*fakes*/*mocks* con la biblioteca estándar), sin dependencias de prueba externas. Se ejecutan con `pytest tests/ -v` y deben pasar al 100% antes de cualquier merge."*
- **Justificación**: Garantiza la verificación exhaustiva de los Requisitos Funcionales RF-01 a RF-04 (resiliencia del bucle, códigos de salida CLI y captura de Ctrl+C) de forma automatizada y sin instalar ningún paquete adicional fuera de los ya estipulados.
- **Alternativa descartada**: No probar el controlador y depender exclusivamente de pruebas manuales. Descartada porque dejaría sin protección de regresión la lógica central del patrón MVC.

### Decisión 4: Reubicación de la orquestación fuera de `main.py`
- **Elección**: Trasladar toda la lógica de flujo a `controllers/download_controller.py`, reduciendo `main.py` a un simple script ensamblador de dependencias de menos de 35 líneas.
- **Justificación**: Cumple con el objetivo fundamental de la especificación: `main.py` queda totalmente libre de lógica de presentación y de negocio, permitiendo cambiar la vista o el modo de arranque sin tocar el controlador.
- **Alternativa descartada**: Dejar el controlador como funciones sueltas dentro de `main.py`. Descartada porque perpetuaría el acoplamiento existente.

---

## 6. Estrategia de tests con `pytest tests/ -v`

Toda la suite de pruebas se ejecuta de forma reproducible con `pytest tests/ -v` sin dependencias externas, alcanzando el 100% de éxito.

### Matriz de Pruebas Automatizadas:

| Archivo de Test | Alcance y Casos a probar | RF Cubierto |
| :--- | :--- | :--- |
| **`tests/test_events.py`** | 1. Instanciación correcta de `ProgressEvent` con valores completos y valores parciales.<br>2. Verificación de inmutabilidad (`frozen=True`).<br>3. Comprobación de que `DownloadPhase` contiene todos los estados requeridos. | **RF-05** |
| **`tests/test_file_manager.py`** | 1. `scan_audio_downloads` filtra correctamente `.mp3`, `.m4a`, `.opus` e ignora otros archivos (`.txt`, `.jpg`, `.part`).<br>2. `scan_audio_downloads` retorna lista vacía si el directorio no existe o no tiene audios.<br>3. `find_partial_download_files` detecta únicamente archivos modificados después del timestamp de inicio.<br>4. `cleanup_files` borra archivos huérfanos sin elevar excepciones si alguno ya fue borrado. | **RF-03**, **RF-06** |
| **`tests/test_controller.py`** | 1. **Modo CLI Directo exitoso**: Invocación directa que simula descarga exitosa; verifica retorno de código de salida `0` y llamada a `show_single_success` sin desplegar menús (**RF-04**).<br>2. **Modo CLI con fallo de red**: Simula excepción operativa; verifica retorno de código `1`, reporte de error en vista y llamada a limpieza de temporales (**RF-03**, **RF-04**).<br>3. **Modo CLI con Ctrl+C**: Simula `KeyboardInterrupt`; verifica retorno de código `130` y limpieza de temporales (**RF-03**, **RF-04**).<br>4. **Bucle Interactivo con entrada vacía**: Usuario ingresa espacio vacío, el controlador re-solicita el dato sin salir del bucle (**RF-02**).<br>5. **Bucle Interactivo con escape 'cancelar'**: Usuario escribe 'cancelar', el controlador regresa al menú principal (**RF-02**).<br>6. **Bucle Interactivo con Ctrl+C durante descarga**: Simula `KeyboardInterrupt` durante descarga; el controlador limpia temporales, emite aviso y regresa al menú interactivo sin terminar la aplicación (**RF-03**).<br>7. **Playlist sin pistas disponibles**: Simula respuesta de lista vacía; el controlador muestra aviso informativo y regresa al menú (**RF-07**).<br>8. **Fallo de FFmpeg en interactivo**: Diagnóstico presentado al usuario y retorno limpio al menú (**RF-02**). | **RF-01**, **RF-02**, **RF-03**, **RF-04**, **RF-07** |
| **Tests Existentes** | Mantener 100% de pase en los 48 tests actuales (`test_platform_validator.py`, `test_validator.py`, `test_format_validator.py`, `test_resolver.py`, `test_qa_edge_cases.py`, etc.). | **No regresión** |

### Implementación del `FakeView` para pruebas:

```python
class FakeView:
    """Implementación en memoria de ViewInterface para testing unitario determinista."""
    def __init__(self, inputs: Optional[List[str]] = None):
        self.inputs = inputs or []
        self.messages_info: List[str] = []
        self.messages_warning: List[str] = []
        self.messages_error: List[str] = []
        self.progress_events: List[ProgressEvent] = []
        self.shown_menus: int = 0
        self.single_successes: List[Dict[str, Any]] = []

    def show_banner(self) -> None: pass
    def show_main_menu(self) -> str:
        self.shown_menus += 1
        return self.inputs.pop(0) if self.inputs else "3"
    def prompt_platform(self) -> str:
        return self.inputs.pop(0) if self.inputs else "youtube"
    def prompt_query(self, platform_name: str) -> str:
        return self.inputs.pop(0) if self.inputs else "test song"
    def prompt_playlist_limit(self) -> Optional[int]:
        return int(self.inputs.pop(0)) if self.inputs else None
    def prompt_audio_format(self, is_playlist: bool) -> str:
        return self.inputs.pop(0) if self.inputs else "mp3"
    def show_platform_mismatch(self, selected: str, adapted: str) -> None: pass
    def show_info(self, message: str) -> None:
        self.messages_info.append(message)
    def show_warning(self, message: str) -> None:
        self.messages_warning.append(message)
    def show_error(self, message: str, error_type: Optional[str] = None) -> None:
        self.messages_error.append(message)
    def show_single_success(self, result: Dict[str, Any]) -> None:
        self.single_successes.append(result)
    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None: pass
    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None: pass
    def show_empty_downloads(self) -> None: pass
    def on_progress(self, event: ProgressEvent) -> None:
        self.progress_events.append(event)
    def start_progress_task(self, title: str, total: Optional[int] = None) -> None: pass
    def stop_progress_task(self) -> None: pass
```

---

## 7. Verificación del Plan contra la Constitución

- **Principio 1 (Stack mínimo)**: ✅ No se añaden librerías externas a `requirements.txt`. El desacoplamiento utiliza `typing.Protocol`, `dataclasses`, `enum` y la biblioteca estándar de Python.
- **Principio 2 (La spec manda)**: ✅ Cubre estrictamente todos los requisitos (RF-01 a RF-07) de `specs/003-MVC/spec.md`. Se programa la actualización de `AGENTS.md` como entregable.
- **Principio 3 (Lógica e interfaz separadas)**: ✅ `core/`, `metadata/` y `utils/` no tienen ninguna referencia ni import hacia `ui/` ni `controllers/`. La vista es inyectada mediante un contrato estructural.
- **Principio 4 (Tests)**: ✅ Se formaliza la enmienda para permitir tests del controlador con *mocks/fakes* en memoria sin instalar librerías adicionales. Ejecución limpia con `pytest tests/ -v`.
- **Principio 5 (Archivos del usuario son sagrados)**: ✅ Coda solo escribe en `downloads/` y `app.log`. Toda cancelación o fallo limpia exclusivamente los residuos huérfanos generados durante la operación.
- **Principio 6 (Español al usuario, inglés al código)**: ✅ Todos los textos de menús, advertencias, tablas y progresos están redactados en español; el código, nombres de clases, métodos, eventos y logs están en inglés.
