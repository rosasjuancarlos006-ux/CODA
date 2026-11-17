# Plan de Implementación Técnica — Interfaz Gráfica de Usuario con Flet (004-GUI)

Este documento establece el diseño de ingeniería, la distribución de módulos, las funciones puras de lógica, los algoritmos en pseudocódigo, la representación visual y la estrategia de verificación automatizada para la construcción de la interfaz gráfica de Coda, en estricto cumplimiento de `specs/004-gui/spec.md` y de los principios de `docs/constitution.md`.

---

## 1. Archivos a crear o modificar y sus responsabilidades

| Archivo | Estado | Responsabilidad y cambios previstos | RF / RNF Cubiertos |
| :--- | :--- | :--- | :--- |
| **`docs/constitution.md`** | **Modificar** | **Enmienda formal de Gobernanza (Regla 1)**: Autorizar explícitamente la incorporación de la librería `flet` para la capa de presentación de escritorio, manteniendo la prohibición de dependencias no autorizadas en el dominio. | **RNF-01**, **Criterio Finalización 1** |
| **`MEMORY.md`** | **Modificar** | **Justificación técnica de dependencias**: Registrar la justificación escrita de la adopción de Flet (Flutter engine embebido para Python, diseño declarativo multiplataforma, reactividad nativa a 60 FPS sin dependencias C complejas). | **RNF-01**, **Criterio Finalización 1** |
| **`AGENTS.md`** | **Modificar** | **Sincronización de arquitectura**: Documentar la coexistencia del modo terminal y el modo gráfico, la estructura del paquete `ui/gui/`, comandos de ejecución y nuevos casos de prueba. | **Criterio Finalización 2** |
| **`requirements.txt`** | **Modificar** | **Gestión de dependencias**: Añadir la versión estable aprobada de `flet>=0.21.0`. | **RNF-01** |
| **`core/queue_manager.py`** | **Crear** | **Gestor puro de la cola de descargas (Dominio)**: Modela de manera inmutable y determinista la cola secuencial FIFO: encolado de tareas, remoción de elementos pendientes por identificador, transición de estados (`PENDING`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `ERROR`) y selección del siguiente ítem. 100% desacoplado de la interfaz. | **RF-04**, **RF-06**, **RF-07**, **RNF-02** |
| **`utils/file_manager.py`** | **Modificar** | **Lógica pura de ficheros y colisiones**: Incorporar función pura `resolve_incremental_filename(dest_dir, filename)` para resolver colisiones mediante sufijos numéricos `Cancion (1).mp3` sin sobreescritura, y `scan_downloaded_files(dest_dir)` con metadatos para la biblioteca. | **RF-09**, **RNF-03**, **Caso Límite 1** |
| **`ui/view_interface.py`** | **Modificar** | **Ampliación del contrato formal**: Incorporar contratos para la visualización de la cola FIFO, notificación de avisos no invasivos (toasts), despliegue de resultados de búsqueda múltiples (top 5) y modales de error con acciones de reintento. | **RF-01**, **RF-03**, **RF-06**, **RF-08**, **RNF-02** |
| **`ui/gui/theme.py`** | **Crear** | **Tokens y estilos del diseño Figma**: Definición de paleta cromática exacta, tipografía, radios de curvatura, espaciados y temas oscuro/claro basados en el prototipo interactivo «CODA». | **RNF-05** |
| **`ui/gui/views/sidebar.py`** | **Crear** | **Componente visual de navegación lateral**: Renderiza la barra lateral con accesos a Inicio, Descargas, Archivos, insignia «CODA · v1.0» y la tarjeta informativa de solo descargas sin reproductor. | **RF-01**, **RNF-05** |
| **`ui/gui/views/home_view.py`** | **Crear** | **Componente visual de Inicio**: Entrada de URL, botón de pegar del portapapeles, botón «Analizar enlace», conmutador a búsqueda y lista de descargas recientes. | **RF-01**, **RF-02**, **RNF-05** |
| **`ui/gui/views/search_view.py`** | **Crear** | **Componente visual de Búsqueda y Resultados**: Campo de texto de búsqueda y renderizado vertical de las 5 mejores tarjetas de coincidencia con botón «Elegir audio». | **RF-03**, **RNF-05** |
| **`ui/gui/views/options_view.py`** | **Crear** | **Componente visual de Opciones**: Radio buttons de plataforma (YouTube / YouTube Music), formato (MP3, M4A, OPUS), calidad automática, campo numérico de límite de playlists y botones de acción. | **RF-04**, **RNF-05** |
| **`ui/gui/views/downloads_view.py`** | **Crear** | **Componente visual de Descargas**: Monitor en tiempo real de la tarea activa (barra, %, MB, velocidad, tiempo, botón cancelar) y lista de elementos pendientes FIFO con botón individual de remoción. | **RF-05**, **RF-06**, **RF-07**, **RNF-05** |
| **`ui/gui/views/files_view.py`** | **Crear** | **Componente visual de Biblioteca**: Listado con auto-refresco de archivos de audio locales, formato, duración, estado y botón para abrir la carpeta física en el explorador de Windows. | **RF-09**, **RNF-03**, **RNF-05** |
| **`ui/gui/flet_view.py`** | **Crear** | **Adaptador principal de Vista Flet**: Implementa formalmente `ViewInterface`, gestiona las vistas de Flet, conmutación de paneles, modales de diálogo y banners de notificación. | **RF-01**, **RF-08**, **RNF-02**, **RNF-04** |
| **`controllers/gui_controller.py`** | **Crear** | **Controlador de interfaz gráfica**: Orquesta eventos de la UI, administra el despachador de la cola de descargas en hilos de trabajo independientes (`threading.Thread` / `asyncio`) para mantener 60 FPS, maneja cancelaciones y actualiza la vista. | **RF-04**, **RF-05**, **RF-06**, **RF-07**, **RF-08**, **RNF-06** |
| **`main.py`** | **Modificar** | **Bootstrap unificado**: Si se recibe argumento de terminal, ejecuta el controlador CLI con `TerminalView`; si no hay argumentos (o `--gui`), arranca la aplicación Flet con `GUIController` y `FletView`. Cero regresiones. | **RF-01**, **RNF-02** |
| **`tests/test_queue_manager.py`** | **Crear** | **Pruebas unitarias del gestor de cola FIFO**: Tests de orden de inserción, remoción por ID, transición de estados, cancelación con elementos remanentes y vaciado seguro. | **RF-06**, **RF-07** |
| **`tests/test_file_collisions.py`** | **Crear** | **Pruebas unitarias de resolución de nombres**: Tests de colisiones consecutivas, sufijos incrementales `(1)`, `(2)`, preservación de archivos originales y caracteres reservados. | **Caso Límite 1**, **RNF-03** |
| **`tests/test_gui_adapter.py`** | **Crear** | **Pruebas unitarias headless del adaptador de vista**: Verificación en memoria de suscripción a eventos, emisión de diálogos y formateo en español sin inicializar ventana física. | **RF-01**, **RF-08**, **RNF-04**, **RNF-07** |

---

## 2. Funciones puras de lógica (Módulos de Dominio y Utilidades)

En estricta observancia de la **Regla 3** (Lógica e interfaz separadas) y la **Regla 4** (Pruebas unitarias sin dependencias externas):

### En `core/queue_manager.py`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class QueueItemStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass(frozen=True)
class QueueItem:
    item_id: str
    title: str
    url_or_query: str
    platform: str
    audio_format: str
    quality: str
    playlist_limit: int
    duration_str: str
    thumbnail_url: Optional[str] = None
    status: QueueItemStatus = QueueItemStatus.PENDING
    error_message: Optional[str] = None
```

#### 2.1. `add_to_queue(queue: List[QueueItem], new_item: QueueItem) -> List[QueueItem]`
- **Responsabilidad**: Función pura que añade una nueva tarea al final de la colección respetando el orden FIFO y validando la unicidad del `item_id`.
- **Parámetros**:
  - `queue` (`List[QueueItem]`): Lista inmutable o previa de tareas.
  - `new_item` (`QueueItem`): Elemento a encolar con estado inicial `PENDING`.
- **Retorno**: Nueva lista con el elemento agregado al final.
- **RF Cubierto**: **RF-04**, **RF-06**.

#### 2.2. `remove_from_queue(queue: List[QueueItem], item_id: str) -> List[QueueItem]`
- **Responsabilidad**: Función pura que extrae un elemento pendiente por su identificador. Si el elemento ya está `ACTIVE`, no lo elimina directamente (debe pasar por cancelación formal).
- **Parámetros**:
  - `queue` (`List[QueueItem]`): Lista actual de tareas.
  - `item_id` (`str`): Identificador único de la tarea a remover.
- **Retorno**: Nueva lista sin el elemento descartado.
- **RF Cubierto**: **RF-06**, **Caso Límite 2**.

#### 2.3. `get_next_pending_item(queue: List[QueueItem]) -> Optional[QueueItem]`
- **Responsabilidad**: Obtiene la primera tarea con estado `PENDING` según la secuencia de entrada FIFO.
- **Parámetros**:
  - `queue` (`List[QueueItem]`): Lista de tareas.
- **Retorno**: El primer `QueueItem` en espera o `None` si la cola está vacía.
- **RF Cubierto**: **RF-06**.

#### 2.4. `update_item_status(queue: List[QueueItem], item_id: str, new_status: QueueItemStatus, error_msg: Optional[str] = None) -> List[QueueItem]`
- **Responsabilidad**: Función pura que produce una nueva lista de tareas con el estado actualizado del elemento especificado.
- **Parámetros**:
  - `queue` (`List[QueueItem]`): Lista actual.
  - `item_id` (`str`): Identificador del elemento a modificar.
  - `new_status` (`QueueItemStatus`): Nuevo estado a asignar.
  - `error_msg` (`Optional[str]`): Mensaje descriptivo opcional si el estado es `ERROR`.
- **Retorno**: Nueva lista con la tarea actualizada.
- **RF Cubierto**: **RF-05**, **RF-06**, **RF-07**, **RF-08**.

---

### En `utils/file_manager.py`:

#### 2.5. `resolve_incremental_filename(dest_dir: Path, base_title: str, extension: str) -> Path`
- **Responsabilidad**: Función pura que determina la ruta definitiva del archivo evitando colisiones físicas. Si `Cancion.mp3` existe en `dest_dir`, evalúa secuencialmente `Cancion (1).mp3`, `Cancion (2).mp3`, etc., retornando la primera ruta disponible sin modificar archivos previos.
- **Parámetros**:
  - `dest_dir` (`Path`): Directorio destino (`downloads/`).
  - `base_title` (`str`): Título ya saneado de caracteres reservados de Windows.
  - `extension` (`str`): Extensión del archivo con punto (ej. `.mp3`).
- **Retorno**: `Path` absoluto único no existente.
- **RF Cubierto**: **Caso Límite 1**, **RNF-03**.

#### 2.6. `scan_downloaded_audio_metadata(dest_dir: Path) -> List[dict]`
- **Responsabilidad**: Escanea el directorio `downloads/` filtrando exclusivamente extensiones soportadas (`.mp3`, `.m4a`, `.opus`), ordenando por fecha de modificación descendente (más recientes primero) y empaquetando nombre, formato, tamaño legible y fecha para la vista.
- **Parámetros**:
  - `dest_dir` (`Path`): Carpeta de descargas.
- **Retorno**: Lista estructurada de diccionarios con metadatos seguros de lectura.
- **RF Cubierto**: **RF-09**, **RNF-03**, **Caso Límite 4**.

---

### En `utils/validator.py`:

#### 2.7. `clean_mixed_url(input_url: str) -> Tuple[str, bool]`
- **Responsabilidad**: Función pura que analiza una dirección web. Si detecta un enlace mixto (`watch?v=ID&list=RD...` o similar), extrae el video individual limpio `watch?v=ID` y reporta mediante una bandera booleana que se aplicó la poda.
- **Parámetros**:
  - `input_url` (`str`): URL suministrada por el usuario.
- **Retorno**: Tupla `(url_limpia, fue_podada)`.
- **RF Cubierto**: **RF-02**, **Caso Límite 5**.

---

## 3. Algoritmo de la interfaz en pseudocódigo

### Algoritmo 1: Orquestación de la Cola FIFO en Segundo Plano (`GUIController`)

```text
ALGORITMO DespachadorDeCola (QueueDispatcherWorker):
    MIENTRAS la_aplicacion_este_activa:
        item_actual = get_next_pending_item(cola_descargas)
        
        SI item_actual ES NULO:
            esperar_evento_de_nueva_tarea_o_tiempo(500 ms)
            CONTINUAR
            
        // Iniciar tarea activa
        cola_descargas = update_item_status(cola_descargas, item_actual.item_id, ACTIVE)
        vista.notificar_cambio_de_cola(cola_descargas)
        vista.establecer_tarea_activa(item_actual)
        
        token_cancelacion = CrearTokenCancelacion()
        
        INTENTAR:
            // Ejecutar descarga desacoplada emitiendo eventos a la vista
            resultado = motor_descarga.descargar(
                query=item_actual.url_or_query,
                platform=item_actual.platform,
                audio_format=item_actual.audio_format,
                playlist_limit=item_actual.playlist_limit,
                callback_progreso=vista.actualizar_progreso,
                token_cancelacion=token_cancelacion
            )
            
            cola_descargas = update_item_status(cola_descargas, item_actual.item_id, COMPLETED)
            vista.notificar_descarga_exitosa(item_actual, resultado)
            
        CAPTURAR CancelacionExcepcion:
            file_manager.limpiar_temporales(directorio_descargas, item_actual.item_id)
            cola_descargas = update_item_status(cola_descargas, item_actual.item_id, CANCELLED)
            
            SI existen_items_pendientes(cola_descargas):
                vista.mostrar_aviso_no_invasivo("Descarga cancelada. Iniciando siguiente pista.")
                // Continua el bucle FIFO
            SINO:
                vista.mostrar_aviso_no_invasivo("Descarga cancelada.")
                vista.navegar_a_seccion("inicio")
                
        CAPTURAR ErrorOperativoExcepcion COMO err:
            file_manager.limpiar_temporales(directorio_descargas, item_actual.item_id)
            cola_descargas = update_item_status(cola_descargas, item_actual.item_id, ERROR, err.mensaje)
            
            // Mostrar modal interactivo con opciones de acción
            opcion = vista.mostrar_modal_error(
                titulo="Error en la descarga",
                mensaje=err.mensaje,
                botones=["Reintentar", "Descartar y continuar"]
            )
            
            SI opcion == "Reintentar":
                cola_descargas = update_item_status(cola_descargas, item_actual.item_id, PENDING)
            SINO:
                // Se descarta y el despachador continúa con la siguiente encolada
                PASAR
                
        FINALMENTE:
            vista.notificar_cambio_de_cola(cola_descargas)
```

---

### Algoritmo 2: Encolado de Descarga desde Pantalla de Opciones

```text
ALGORITMO AlPulsarIniciarDescarga (OpcionesView):
    datos_config = capturar_valores_formulario()
    // datos_config: {origen, formato, limite_playlist, pista_seleccionada}
    
    nuevo_item = CrearQueueItem(
        item_id=generar_uuid(),
        title=datos_config.pista.titulo,
        url_or_query=datos_config.pista.enlace,
        platform=datos_config.origen,
        audio_format=datos_config.formato,
        quality="auto",
        playlist_limit=datos_config.limite_playlist,
        duration_str=datos_config.pista.duracion,
        status=PENDING
    )
    
    hay_tarea_en_curso = controlador.hay_tarea_activa()
    controlador.encolar_tarea(nuevo_item)
    
    SI NO hay_tarea_en_curso:
        // Primera descarga: redirige de inmediato a la sección de seguimiento
        controlador.navegar_a_seccion("descargas")
    SINO:
        // Descarga concurrente en cola: no interrumpe el flujo del usuario
        controlador.mostrar_aviso_toast("Agregado a la cola de descargas")
        controlador.navegar_a_vista_previa() // Retorna a Inicio o Búsqueda
```

---

### Algoritmo 3: Búsqueda y Despliegue de los 5 Mejores Resultados

```text
ALGORITMO EjecutarBusquedaPorTexto (SearchView):
    termino = campo_texto.valor.trim()
    SI termino ES VACIO:
        RETORNAR
        
    vista.mostrar_indicador_busqueda(activo=VERDADERO)
    
    INTENTAR:
        // Llamada asíncrona al resolver sin congelar la UI
        resultados = resolver.buscar_top_coincidencias(termino, limite=5)
        
        SI longitud(resultados) == 0:
            vista.mostrar_modal_error(
                titulo="Sin coincidencias",
                mensaje="No se encontraron canciones para el término indicado.",
                botones=["Nueva búsqueda"]
            )
        SINO:
            vista.renderizar_lista_vertical_resultados(resultados)
            
    CAPTURAR ErrorRedExcepcion COMO e:
        vista.mostrar_modal_error(
            titulo="Error de conexión",
            mensaje="No fue posible conectar con el servicio de búsqueda. Verifica tu red.",
            botones=["Reintentar", "Cancelar"]
        )
        
    FINALMENTE:
        vista.mostrar_indicador_busqueda(activo=FALSO)
```

---

## 4. Cómo se pinta en la interfaz (Mapeo Figma a Componentes Flet)

Fielmente derivado de la inspección del prototipo Figma `Zgc9KuB7ncqjHbjhcaITyF` («CODA»):

```
+---------------------------------------------------------------------------------------------------+
|  [Logo CODA]  CODA · Tu música, en tus archivos.                       [ — ] [ 口 ] [ X ]        |
+-------------------+-------------------------------------------------------------------------------+
|  TU ESPACIO       |  [ Cabecera contextual: "Descarga tu música" / Fuentes: YouTube & Music ]      |
|                   |-------------------------------------------------------------------------------|
|  (•) Inicio       |                                                                               |
|                   |  [ Enlace y Búsqueda ]                                                        |
|  ( ) Descargas    |  +-------------------------------------------------------------------------+  |
|                   |  | [Tab: Pegar enlace]   [Tab: Buscar por nombre]                          |  |
|  ( ) Archivos     |  |                                                                         |  |
|                   |  | [ Input: "Pega aquí tu enlace..."           ] [ Pegar ] [ Analizar ]    |  |
|                   |  +-------------------------------------------------------------------------+  |
|                   |                                                                               |
|                   |  [ Descargas recientes / Biblioteca rápida ]                                  |
|                   |  +-------------------------------------------------------------------------+  |
|                   |  | TÍTULO                   FORMATO       DURACIÓN       ESTADO                |  |
|  [ Card Offline ] |  | Noches de neón           MP3           3:42           [Completada] [Abrir]  |  |
|  "Solo descargas. |  | Sesiones para...         M4A           12 canciones   [Completada] [Abrir]  |  |
|  Sin reproductor" |  +-------------------------------------------------------------------------+  |
|                   |                                                                               |
|  CODA · v1.0      |  Nota de uso: "Descarga solo contenido propio..."      Destino: downloads/    |
+-------------------+-------------------------------------------------------------------------------+
```

### Componentes de diseño declarativo en Flet:

1. **Tokens y paleta (en `theme.py`)**:
   - `BG_DARK = "#121214"`, `SURFACE_COLOR = "#1A1A1E"`, `ACCENT_COLOR = "#E24A4A"` (o acento corporativo CODA), `TEXT_PRIMARY = "#FFFFFF"`, `TEXT_MUTED = "#8E8E93"`, `BORDER_COLOR = "#2C2C30"`.
   - `BorderRadius`: Contenedores principales `12px`, botones `8px`, badges `4px`.
   - `TextStyle`: Tipografía sans-serif con jerarquía clara (Títulos: 24sp semibold, Subtítulos: 14sp regular, Metadatos: 11sp uppercase).

2. **Estructura de Ventana (`ft.Row(expand=True)`)**:
   - **Columna izquierda fija (`width=200`, `NavigationRail` / `Container`)**:
     - Logo CODA con icono de onda sonora / clave musical.
     - Sección "TU ESPACIO" con botones interactivos de selección activa: `Inicio`, `Descargas` (con badge numérico de tareas pendientes si hay cola), `Archivos`.
     - Tarjeta inferior informativa: `Container(border_radius=8, bgcolor=SURFACE_COLOR)` con texto pedagógico: *"Solo descargas. Sin reproductor integrado."*
     - Etiqueta de versión: `CODA · v1.0`.
   - **Área central dinámica (`ft.AnimatedSwitcher` o contenedor conmutado)**:
     - Renderiza según el estado activo: `HomeView`, `SearchView`, `OptionsView`, `DownloadsView` o `FilesView`.

3. **Pantalla de Resultados de Búsqueda (`SearchView`)**:
   - `ft.ListView(spacing=10)` con los 5 mejores resultados.
   - Cada elemento es una tarjeta horizontal (`ft.Card` / `ft.Container` con padding interno de 16px):
     - Icono de pista / thumbnail pequeño (56x56 px con fallback seguro a icono genérico).
     - Columna con título en negrita, artista/canal y duración (ej. `3:42`).
     - Botón derecho `ft.ElevatedButton("Elegir audio")` que transiciona a `OptionsView`.

4. **Pantalla de Opciones de Descarga (`OptionsView`)**:
   - Tarjeta resumen de la canción o playlist elegida.
   - Bloque 01: Radio buttons horizontales para origen (`YouTube` vs `YouTube Music`).
   - Bloque 02: Radio buttons para formato (`MP3`, `M4A`, `OPUS`).
   - Bloque 03: Indicador de calidad automática (texto informativo: *"Mejor disponible en la fuente"*).
   - Bloque 04 (Condicional): Si es playlist, campo numérico `ft.TextField(label="Límite de canciones", hint_text="Todas por defecto")`.
   - Botones inferiores: `ft.OutlinedButton("Cancelar")` y `ft.ElevatedButton("Iniciar descarga", bgcolor=ACCENT_COLOR)`.

5. **Pantalla de Monitor de Descargas (`DownloadsView`)**:
   - **Tarjeta de Descarga Activa**:
     - Título y artista con badge de fase activa: `PREPARING`, `DOWNLOADING`, `CONVERTING`, `METADATA`.
     - Barra continua `ft.ProgressBar(value=porcentaje / 100.0)`.
     - Grilla métrica: Transferido (ej. `6,8 de 10 MB`), Velocidad (`1,6 MB/s`), Tiempo restante (`Unos segundos`).
     - Botón `ft.ElevatedButton("Cancelar descarga")` con icono de parada.
   - **Lista de Cola FIFO (`ft.ListView`)**:
     - Título: *"En cola de espera (N canciones)"*.
     - Tarjetas compactas de pistas pendientes mostrando posición (1, 2, 3...), título, formato y botón de remoción rápida `ft.IconButton(ft.icons.CLOSE)` para descartar la canción antes de que inicie.

6. **Pantalla de Biblioteca (`FilesView`)**:
   - Cabecera con contador de descargas completadas y botón principal `ft.ElevatedButton("Abrir carpeta")` que invoca `os.startfile(DOWNLOADS_DIR)` en Windows.
   - Tabla estructurada con auto-refresco en cada visita: Icono de audio, Nombre de archivo, Formato, Duración, Estado (`Guardado`). Sin botones de modificación ni borrado.

7. **Diálogos Modales (`ft.AlertDialog`)**:
   - Modal de error con título en español, ícono de alerta, texto descriptivo del incidente y dos botones de acción: `ft.TextButton("Reintentar")` y `ft.ElevatedButton("Aceptar / Volver")`.

---

## 5. Decisiones técnicas justificadas y alternativas descartadas

### 5.1. Adopción de Python Flet para la GUI
- **Decisión**: Utilizar `flet` como framework declarativo para la interfaz de usuario.
- **Justificación**: Flet compila internamente sobre Flutter, ofreciendo un renderizado nativo por GPU a 60 FPS con componentes modernos idénticos al prototipo Figma (sombras suaves, bordes redondeados, barras de progreso fluidas, temas oscuros refinados) sin lidiar con estilos rústicos de Tkinter ni complejas instalaciones binarias multiplataforma de Qt.
- **Alternativas descartadas**:
  - *Tkinter / CustomTkinter*: Descartado por limitaciones severas en layouts complejos, dificultades para emular componentes modernos tipo tarjeta y soporte asíncrono deficiente que congela la ventana durante descargas de red.
  - *PyQt / PySide6*: Descartado por licenciamiento complejo (GPL/LGPL), peso excesivo de instalación (+100 MB de binarios) y curva elevada para el mantenimiento de estilos CSS personalizados.

### 5.2. Cola de Descargas Secuencial en memoria vs. Multidescarga paralela
- **Decisión**: Procesamiento estrictamente secuencial FIFO administrado por un hilo despachador de segundo plano (`threading.Thread`), permitiendo encolar y remover tareas libremente desde la UI.
- **Justificación**: Respeta taxativamente la decisión de alcance acordada. Descargar múltiples streams de YouTube en paralelo satura el ancho de banda del usuario, aumenta drásticamente el riesgo de *rate-limiting* (baneo temporal de IP o errores 429 por parte de YouTube) y multiplica el uso de CPU al transcodificar con FFmpeg concurrentemente.
- **Alternativas descartadas**:
  - *Pool de concurrencia paralela (`ThreadPoolExecutor` con N descargas simultáneas)*: Descartada explícitamente para evitar throttling de red y corrupción de recursos.
  - *Persistencia de cola en base de datos local SQLite*: Descartada para evitar añadir capas de almacenamiento innecesarias en esta versión; la cola opera limpiamente en memoria durante la sesión activa.

### 5.3. Poda automática de mixes (`clean_mixed_url`) en la captura de enlaces
- **Decisión**: Detectar automáticamente enlaces con `list=RD...` y extraer únicamente el identificador del video individual.
- **Justificación**: Los mixes generados por el algoritmo de YouTube Music son listas infinitas no intencionadas por el usuario. Preguntar en cada ocasión interrumpe la fluidez, mientras que podar automáticamente garantiza que solo se descargue la canción deseada, igual que en la experiencia probada de terminal.
- **Alternativa descartada**:
  - *Diálogo modal de confirmación en cada enlace mixto*: Descartado porque ralentiza la experiencia de usuario y confunde a quienes no comprenden la diferencia técnica entre una lista manual y un mix dinámico de radio.

### 5.4. Resolución de duplicados mediante sufijos incrementales `(1)`
- **Decisión**: Si el archivo ya existe físicamente en `downloads/`, renombrar automáticamente la nueva descarga a `Titulo (1).ext`.
- **Justificación**: Cumple al 100% con la Regla 5 de la Constitución (*«Los archivos del usuario son sagrados»*). La sobrescritura destruiría archivos previos sin consentimiento, y omitir la descarga impediría que el usuario descargue una versión con diferente calidad o bitrate.
- **Alternativa descartada**:
  - *Sobrescritura silenciosa*: Descartada por violar la integridad de archivos del usuario.
  - *Modal de confirmación de sobrescritura*: Descartado porque bloquearía la cola de descargas automática en segundo plano si el usuario dejó la aplicación descargando desatendida.

---

## 6. Estrategia de tests automatizados (`pytest tests/ -v`)

En estricta observancia de la **Regla 4** de la Constitución: las pruebas no deben requerir dependencias de prueba externas ni abrir ventanas gráficas físicas (ejecución 100% *headless*).

### 6.1. Pruebas unitarias de dominio puro (`tests/test_queue_manager.py`)
- **`test_add_to_queue_fifo_order`**: Verifica que las tareas se agregan manteniendo el orden secuencial estricto de llegada.
- **`test_remove_pending_item`**: Verifica que una canción con estado `PENDING` puede ser removida por su ID sin afectar a las demás.
- **`test_remove_active_item_prevented`**: Comprueba que una tarea en estado `ACTIVE` no puede ser purgada directamente con la función de remoción (requiere cancelación formal).
- **`test_get_next_pending_item_empty`**: Verifica que retorna `None` cuando no hay elementos pendientes.
- **`test_update_status_transitions`**: Comprueba transiciones válidas (`PENDING` -> `ACTIVE` -> `COMPLETED` / `CANCELLED` / `ERROR`).

### 6.2. Pruebas unitarias de colisión de archivos (`tests/test_file_collisions.py`)
- **`test_unique_filename_when_no_collision`**: Comprueba que si `Pista.mp3` no existe, retorna la ruta original sin modificaciones.
- **`test_incremental_suffix_single_collision`**: Simula la existencia de `Pista.mp3` y verifica que genera `Pista (1).mp3`.
- **`test_incremental_suffix_multiple_collisions`**: Simula `Pista.mp3`, `Pista (1).mp3`, `Pista (2).mp3` y comprueba que genera `Pista (3).mp3`.
- **`test_sanitization_with_reserved_characters`**: Verifica que caracteres reservados en Windows (`:`, `*`, `?`, `/`, `\`) se limpian antes de resolver el sufijo.

### 6.3. Pruebas unitarias del analizador de enlaces (`tests/test_url_cleaner.py`)
- **`test_clean_mixed_url_with_rd_playlist`**: Verifica que `https://music.youtube.com/watch?v=abc&list=RDabc` se poda a `https://music.youtube.com/watch?v=abc` reportando `fue_podada=True`.
- **`test_clean_mixed_url_normal_playlist`**: Verifica que enlaces de listas genuinas `playlist?list=PL...` no son alterados y reportan `fue_podada=False`.
- **`test_clean_mixed_url_single_video`**: Verifica que enlaces de video sin lista permanecen intactos.

### 6.4. Pruebas unitarias headless del adaptador de vista (`tests/test_gui_adapter.py`)
- **`test_flet_view_implements_view_interface`**: Validación estructural (usando `isinstance` / `issubclass` sobre `ViewInterface`) de que el adaptador gráfico implementa todos los métodos requeridos por el contrato.
- **`test_gui_event_consumption_in_memory`**: Emite eventos `ProgressEvent` a la vista simulada en memoria y valida la actualización de variables reactivas internas sin llamar al bucle visual de Flutter.
- **`test_spanish_text_enforcement_in_gui_strings`**: Inspecciona los literales del tema y vistas verificando la ausencia de mensajes en inglés hacia el usuario.

### 6.5. Comando de verificación integral
Toda la suite debe pasar al 100% en consola sin warnings ni fallos:
```powershell
pytest tests/ -v
```

---

## 7. Mapeo de Cobertura de Requisitos Funcionales

| Requisito Funcional | Módulo / Componente Técnico | Cómo se satisface en el Plan |
| :--- | :--- | :--- |
| **RF-01 (Ventana y navegación)** | `ui/gui/views/sidebar.py`, `flet_view.py` | Contenedor de ventana personalizada, barra lateral con Inicio, Descargas, Archivos, badge de versión e indicación de solo descargas. |
| **RF-02 (Captura y saneamiento)** | `ui/gui/views/home_view.py`, `utils/validator.py` | Campo de URL, integración con portapapeles, poda automática de mixes con `clean_mixed_url` y modal de enlace inválido. |
| **RF-03 (Búsqueda interactiva top 5)**| `ui/gui/views/search_view.py`, `core/resolver.py` | Entrada de texto, consulta a resolver y renderizado vertical de 5 tarjetas con título, artista, duración y botón «Elegir audio». |
| **RF-04 (Opciones y encolado)** | `ui/gui/views/options_view.py`, `core/queue_manager.py` | Selección de plataforma y formato, límite opcional de playlists, redirección directa si es la primera tarea o toast no invasivo si hay tareas activas. |
| **RF-05 (Monitor en tiempo real)** | `ui/gui/views/downloads_view.py`, `core/events.py` | Proyección reactiva de eventos `ProgressEvent` (%, MB transferidos, velocidad, tiempo restante y pasos de fases). |
| **RF-06 (Cola secuencial FIFO)** | `core/queue_manager.py`, `controllers/gui_controller.py` | Despachador en hilo secundario de procesamiento estrictamente secuencial de tareas con botón de remoción anticipada en la lista. |
| **RF-07 (Cancelación y purga)** | `controllers/gui_controller.py`, `utils/file_manager.py` | Botón «Cancelar descarga» activo, interrupción limpia, purga de temporales y transición a la siguiente encolada o a Inicio. |
| **RF-08 (Gestión modal de fallos)** | `ui/gui/flet_view.py`, `controllers/gui_controller.py` | Diálogos modales interactivos en primer plano con botones «Reintentar» y «Descartar / Volver», registro en `app.log`. |
| **RF-09 (Biblioteca con auto-refresco)**| `ui/gui/views/files_view.py`, `utils/file_manager.py` | Escaneo en cada visita de `downloads/`, listado de audios soportados, botón «Abrir carpeta» nativo de Windows y prohibición total de borrado/edición desde la UI. |
