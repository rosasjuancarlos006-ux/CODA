# Tareas de Implementación — Interfaz Gráfica de Usuario (004-GUI)

Lista de tareas secuenciales organizadas por dependencias lógicas. Cada tarea está acotada para completarse en un intervalo de 20 a 30 minutos y cuenta con su respectivo mapeo a los Requisitos Funcionales (RF) y un criterio de aceptación verificable.

---

## Fase A — Gobernanza, dominio puro y utilidades (sin dependencia de Flet)

### Tarea 1: Enmienda constitucional y registro de dependencia
- **Archivos:** `docs/constitution.md`, `MEMORY.md`, `requirements.txt`
- **Requisitos cubiertos:** RNF-01, Criterio Finalización 1
- **Descripción:** Enmendar formalmente la Regla 1 de `docs/constitution.md` para autorizar `flet` como dependencia de producción exclusiva de la capa de presentación gráfica. Añadir `flet>=0.21.0` en `requirements.txt`. Registrar en `MEMORY.md` la justificación técnica de la adopción (Flutter engine embebido, diseño declarativo, reactividad nativa a 60 FPS, sin dependencias C complejas).
- [x] **Hecho cuando:** `python -c "text = open('docs/constitution.md', encoding='utf-8').read().lower(); assert 'flet' in text; print('Enmienda verificada')"` se ejecute con salida 0, y `Select-String -Path requirements.txt -Pattern 'flet'` devuelva coincidencia.

---

### Tarea 2: Modelo puro de la cola de descargas FIFO — Estructuras de datos
- **Archivo:** `core/queue_manager.py`
- **Requisitos cubiertos:** RF-04, RF-06, RNF-02
- **Descripción:** Crear `core/queue_manager.py` con el enumerador `QueueItemStatus` (`PENDING`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `ERROR`) y la dataclass inmutable `QueueItem` (con campos: `item_id`, `title`, `url_or_query`, `platform`, `audio_format`, `quality`, `playlist_limit`, `duration_str`, `thumbnail_url`, `status`, `error_message`). Sin imports de UI.
- [x] **Hecho cuando:** `python -c "from core.queue_manager import QueueItem, QueueItemStatus; item = QueueItem(item_id='1', title='Test', url_or_query='q', platform='youtube', audio_format='mp3', quality='auto', playlist_limit=0, duration_str='3:00'); assert item.status == QueueItemStatus.PENDING; print('Estructuras cargadas')"` se ejecute sin errores.

---

### Tarea 3: Modelo puro de la cola FIFO — Funciones de manipulación
- **Archivo:** `core/queue_manager.py`
- **Requisitos cubiertos:** RF-04, RF-06, RF-07, Caso Límite 2
- **Descripción:** Implementar en `core/queue_manager.py` las funciones puras: `add_to_queue(queue, new_item)` (agrega al final validando unicidad de ID), `remove_from_queue(queue, item_id)` (extrae solo elementos `PENDING`; ignora si está `ACTIVE`), `get_next_pending_item(queue)` (retorna el primer `PENDING` o `None`) y `update_item_status(queue, item_id, new_status, error_msg)` (produce nueva lista con estado actualizado).
- [x] **Hecho cuando:** `python -c "from core.queue_manager import add_to_queue, remove_from_queue, get_next_pending_item, update_item_status; print('Funciones FIFO cargadas')"` se ejecute con salida 0.

---

### Tarea 4: Pruebas unitarias del gestor de cola FIFO
- **Archivo:** `tests/test_queue_manager.py`
- **Requisitos cubiertos:** RF-06, RF-07
- **Descripción:** Crear `tests/test_queue_manager.py` con al menos 6 pruebas: orden FIFO de inserción, remoción de elemento pendiente por ID, protección de elemento activo (no se elimina con `remove_from_queue`), `get_next_pending_item` con cola vacía retorna `None`, transiciones válidas de estado (`PENDING` → `ACTIVE` → `COMPLETED` / `CANCELLED` / `ERROR`), y remoción de un ID inexistente que devuelve la lista sin cambios.
- [x] **Hecho cuando:** `pytest tests/test_queue_manager.py -v` ejecute al menos 6 pruebas y todas pasen al 100%.

---

### Tarea 5: Resolución de colisiones de nombres de archivo con sufijos incrementales
- **Archivo:** `utils/file_manager.py`
- **Requisitos cubiertos:** RNF-03, Caso Límite 1
- **Descripción:** Añadir en `utils/file_manager.py` la función pura `resolve_incremental_filename(dest_dir: Path, base_title: str, extension: str) -> Path`. Si `Cancion.mp3` existe, evalúa secuencialmente `Cancion (1).mp3`, `Cancion (2).mp3`, etc., retornando la primera ruta no existente. Asegurar que el título ya esté saneado de caracteres reservados de Windows antes de la evaluación.
- [x] **Hecho cuando:** `python -c "from utils.file_manager import resolve_incremental_filename; print('Función de colisiones cargada')"` se ejecute con salida 0.

---

### Tarea 6: Escaneo de biblioteca local con metadatos de lectura
- **Archivo:** `utils/file_manager.py`
- **Requisitos cubiertos:** RF-09, RNF-03, Caso Límite 4
- **Descripción:** Añadir en `utils/file_manager.py` la función `scan_downloaded_audio_metadata(dest_dir: Path) -> List[dict]`. Filtra exclusivamente extensiones soportadas (`.mp3`, `.m4a`, `.opus`), ordena por fecha de modificación descendente y empaqueta nombre, formato, tamaño legible y fecha en una lista de diccionarios.
- [x] **Hecho cuando:** `python -c "from utils.file_manager import scan_downloaded_audio_metadata; print('Escaneo de biblioteca cargado')"` se ejecute con salida 0.

---

### Tarea 7: Pruebas unitarias de colisiones de archivos y escaneo de biblioteca
- **Archivo:** `tests/test_file_collisions.py`
- **Requisitos cubiertos:** Caso Límite 1, RNF-03, RF-09
- **Descripción:** Crear `tests/test_file_collisions.py` con al menos 5 pruebas: nombre único sin colisión, sufijo `(1)` ante una colisión, sufijo `(3)` ante tres archivos previos, saneamiento de caracteres reservados de Windows en el título, y escaneo de directorio con archivos mixtos (mp3 + txt) filtrando solo audio.
- [x] **Hecho cuando:** `pytest tests/test_file_collisions.py -v` ejecute al menos 5 pruebas y todas pasen al 100%.

---

### Tarea 8: Ampliación del contrato formal `ViewInterface` para la GUI
- **Archivo:** `ui/view_interface.py`
- **Requisitos cubiertos:** RF-01, RF-03, RF-06, RF-08, RNF-02
- **Descripción:** Ampliar `ViewInterface` con las firmas de métodos necesarias para la GUI: `show_search_results(results: List[dict])`, `show_queue_state(queue: List)`, `show_toast(message: str)`, `show_modal_error(title: str, message: str, buttons: List[str]) -> str`, `navigate_to_section(section: str)`. Preservar intactos todos los métodos existentes usados por `TerminalView`.
- [x] **Hecho cuando:** `python -c "from ui.view_interface import ViewInterface; print('ViewInterface ampliada cargada')"` se ejecute sin errores, y `pytest tests/test_view_interface.py -v` pase al 100%.

---

## Fase B — Tokens visuales, estructura de ventana y navegación

### Tarea 9: Tokens de diseño y tema visual Figma
- **Archivo:** `ui/gui/theme.py` (crear `ui/gui/__init__.py` y `ui/gui/views/__init__.py`)
- **Requisitos cubiertos:** RNF-05
- **Descripción:** Crear el paquete `ui/gui/` con su `__init__.py` y el módulo `theme.py` definiendo constantes de paleta cromática (`BG_DARK`, `SURFACE_COLOR`, `ACCENT_COLOR`, `TEXT_PRIMARY`, `TEXT_MUTED`, `BORDER_COLOR`), radios de curvatura (`RADIUS_CONTAINER`, `RADIUS_BUTTON`, `RADIUS_BADGE`), escala tipográfica (`TITLE_SIZE`, `SUBTITLE_SIZE`, `META_SIZE`) y función `build_coda_theme()` que retorne un `ft.Theme` configurado.
- [x] **Hecho cuando:** `python -c "from ui.gui.theme import BG_DARK, SURFACE_COLOR, ACCENT_COLOR, build_coda_theme; print('Tema Figma cargado')"` se ejecute sin errores.

---

### Tarea 10: Componente de navegación lateral (Sidebar)
- **Archivo:** `ui/gui/views/sidebar.py`
- **Requisitos cubiertos:** RF-01, RNF-05
- **Descripción:** Crear `ui/gui/views/sidebar.py` con una función o clase que construya el contenedor lateral fijo (ancho ~196px) incluyendo: logo CODA, etiqueta «TU ESPACIO», botones de navegación con indicador de selección activa para Inicio, Descargas (con badge numérico de cola) y Archivos, tarjeta informativa «Solo descargas. Sin reproductor integrado.» y etiqueta de versión «CODA · v1.0». Todos los textos en español.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.sidebar import build_sidebar; print('Sidebar cargado')"` se ejecute sin errores.

---

### Tarea 11: Esqueleto de ventana principal y conmutación de paneles
- **Archivo:** `ui/gui/flet_view.py`
- **Requisitos cubiertos:** RF-01, RNF-02, RNF-04
- **Descripción:** Crear `ui/gui/flet_view.py` con la clase `FletView` que implemente `ViewInterface`. Configurar la ventana Flet con título «CODA · Tu música, en tus archivos.», controles de ventana (minimizar, maximizar, cerrar), barra lateral integrada y un contenedor central dinámico que conmute entre las secciones Inicio, Descargas y Archivos sin perder el estado. Implementar `navigate_to_section(section)` y `show_toast(message)` con `ft.SnackBar`.
- [x] **Hecho cuando:** `python -c "from ui.gui.flet_view import FletView; from ui.view_interface import ViewInterface; print('FletView cargada y compatible con ViewInterface')"` se ejecute sin errores.

---

## Fase C — Vistas de contenido (Inicio, Búsqueda, Opciones)

### Tarea 12: Pantalla de Inicio — Campo de enlace y pegado desde portapapeles
- **Archivo:** `ui/gui/views/home_view.py`
- **Requisitos cubiertos:** RF-02, RNF-05
- **Descripción:** Crear `ui/gui/views/home_view.py` con la cabecera contextual («Descarga tu música»), el conmutador de modo (pestaña «Pegar enlace» / «Buscar por nombre»), el campo de texto para URLs con botón «Pegar» (integración con portapapeles del SO) y botón «Analizar enlace», la nota de formatos soportados y la barra inferior de nota de uso y destino de descargas.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.home_view import build_home_view; print('HomeView cargada')"` se ejecute sin errores.

---

### Tarea 13: Pantalla de Inicio — Validación de URL, poda de mixes y tabla de recientes
- **Archivo:** `ui/gui/views/home_view.py`
- **Requisitos cubiertos:** RF-02, Caso Límite 5
- **Descripción:** Integrar la lógica de validación de URL al pulsar «Analizar enlace»: si la URL es vacía o inválida, invocar `show_modal_error`; si contiene `&list=RD...`, aplicar `clean_mixed_url` (poda automática). Añadir la sección «Descargas recientes» con una tabla mostrando las últimas canciones descargadas (título, formato, duración, estado) consumiendo `scan_downloaded_audio_metadata`.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.home_view import build_home_view; print('HomeView con validación cargada')"` se ejecute sin errores.

---

### Tarea 14: Pantalla de Búsqueda — Campo de texto y despliegue de 5 resultados
- **Archivo:** `ui/gui/views/search_view.py`
- **Requisitos cubiertos:** RF-03, RNF-05
- **Descripción:** Crear `ui/gui/views/search_view.py` con el campo de búsqueda por texto, botón «Buscar», indicador visual de consulta en curso y lista vertical de los 5 mejores resultados. Cada tarjeta muestra: icono de audio (con fallback genérico), título en negrita, artista/canal, versión, duración y botón «Elegir audio» que transiciona a la vista de opciones con la pista precargada.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.search_view import build_search_view; print('SearchView cargada')"` se ejecute sin errores.

---

### Tarea 15: Pantalla de Opciones — Plataforma, formato, límite y encolado
- **Archivo:** `ui/gui/views/options_view.py`
- **Requisitos cubiertos:** RF-04, RNF-05
- **Descripción:** Crear `ui/gui/views/options_view.py` con la información de la pista seleccionada, radio buttons de plataforma (YouTube / YouTube Music), radio buttons de formato (MP3 / M4A / OPUS), indicador de calidad automática, campo numérico condicional de límite de playlist (visible solo cuando el contenido es playlist, vacío = descargar todo), texto de carpeta de destino y botones «Cancelar» / «Iniciar descarga».
- [x] **Hecho cuando:** `python -c "from ui.gui.views.options_view import build_options_view; print('OptionsView cargada')"` se ejecute sin errores.

---

## Fase D — Vista de descargas, progreso en tiempo real y cola visual

### Tarea 16: Pantalla de Descargas — Tarjeta de progreso de la tarea activa
- **Archivo:** `ui/gui/views/downloads_view.py`
- **Requisitos cubiertos:** RF-05, RNF-05
- **Descripción:** Crear `ui/gui/views/downloads_view.py` con la tarjeta de descarga activa: título y artista, badge de fase (Preparación / Transferencia / Conversión / Metadatos), barra de progreso continua (`ft.ProgressBar`), grilla de métricas (transferido, velocidad, tiempo restante), indicador de destino y botón «Cancelar descarga». Implementar degradación visual (barra indeterminada + spinner) cuando las métricas numéricas no están disponibles.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.downloads_view import build_downloads_view; print('DownloadsView cargada')"` se ejecute sin errores.

---

### Tarea 17: Pantalla de Descargas — Lista visual de cola FIFO y remoción anticipada
- **Archivo:** `ui/gui/views/downloads_view.py`
- **Requisitos cubiertos:** RF-06, Caso Límite 2
- **Descripción:** Añadir debajo de la tarjeta activa la sección «En cola de espera (N canciones)» con un `ft.ListView` de tarjetas compactas para cada elemento pendiente mostrando posición, título, formato y un botón de remoción rápida (`ft.IconButton(CLOSE)`) que invoca `remove_from_queue` inmediatamente. Agregar indicador de pasos de descarga (Conexión lista → Descargando → Guardar archivo).
- [x] **Hecho cuando:** `python -c "from ui.gui.views.downloads_view import build_downloads_view; print('Cola visual FIFO cargada')"` se ejecute sin errores.

---

### Tarea 18: Pantalla de Descarga Exitosa — Resumen y acciones post-descarga
- **Archivo:** `ui/gui/views/downloads_view.py`
- **Requisitos cubiertos:** RF-05, RF-07
- **Descripción:** Añadir el estado visual de «Descarga exitosa» mostrando el resumen de la pista completada (título, artista, formato, duración, tamaño) con dos botones de acción: «Abrir carpeta» (invoca `os.startfile` en Windows) y «Nueva descarga» (navega a Inicio). Si hay más elementos en la cola, transicionar automáticamente al siguiente sin mostrar pantalla de éxito individual.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.downloads_view import build_downloads_view; print('Estado de éxito cargado')"` se ejecute sin errores.

---

## Fase E — Biblioteca de archivos y diálogos modales

### Tarea 19: Pantalla de Archivos Descargados — Listado, auto-refresco y apertura segura
- **Archivo:** `ui/gui/views/files_view.py`
- **Requisitos cubiertos:** RF-09, RNF-03, Caso Límite 4
- **Descripción:** Crear `ui/gui/views/files_view.py` con cabecera de resumen (contador de descargas, carpeta destino), botón «Abrir carpeta» y botón «Nueva descarga». Tabla de archivos con columnas: Archivo, Tipo, Duración, Estado. Invocación automática de `scan_downloaded_audio_metadata` en cada ingreso o interacción con la sección. Estado vacío informativo si no hay archivos. Ningún botón de borrado, edición ni renombrado.
- [x] **Hecho cuando:** `python -c "from ui.gui.views.files_view import build_files_view; print('FilesView cargada')"` se ejecute sin errores.

---

### Tarea 20: Diálogos modales de error con opciones de acción
- **Archivo:** `ui/gui/flet_view.py`
- **Requisitos cubiertos:** RF-08, RNF-04
- **Descripción:** Implementar en `FletView` el método `show_modal_error(title, message, buttons)` usando `ft.AlertDialog` con título en español, texto descriptivo, ícono de alerta y dos botones: «Reintentar» y «Aceptar / Volver al inicio». Implementar diálogo de confirmación al cerrar la ventana con descargas activas (Caso Límite 9). Todos los textos estrictamente en español.
- [x] **Hecho cuando:** `python -c "from ui.gui.flet_view import FletView; print('Modales de error cargados')"` se ejecute sin errores.

---

## Fase F — Controlador GUI y despachador de la cola

### Tarea 21: Controlador de interfaz gráfica — Estructura base y gestión de estado
- **Archivo:** `controllers/gui_controller.py`
- **Requisitos cubiertos:** RF-04, RF-06, RNF-06
- **Descripción:** Crear `controllers/gui_controller.py` con la clase `GUIController(view: ViewInterface, output_dir: Path)`. Implementar la gestión del estado interno de la cola (lista de `QueueItem`), los métodos `encolar_tarea(item)`, `remover_de_cola(item_id)`, `hay_tarea_activa()` y la lógica de decisión de navegación al encolar (redirigir a Descargas si es la primera tarea; emitir toast no invasivo si ya hay una activa).
- [x] **Hecho cuando:** `python -c "from controllers.gui_controller import GUIController; print('GUIController cargado')"` se ejecute con salida 0.

---

### Tarea 22: Despachador de cola en hilo secundario — Bucle FIFO asíncrono
- **Archivo:** `controllers/gui_controller.py`
- **Requisitos cubiertos:** RF-05, RF-06, RF-07, RF-08, RNF-06
- **Descripción:** Implementar el método `_queue_dispatcher_worker()` ejecutado en `threading.Thread(daemon=True)`. El bucle: obtiene el siguiente ítem pendiente, lo marca `ACTIVE`, ejecuta la descarga delegando al motor con callback de progreso, maneja `CancelacionExcepcion` (purga temporales, inicia la siguiente o navega a Inicio), captura `ErrorOperativoExcepcion` (muestra modal, reintenta o descarta) y en éxito actualiza a `COMPLETED`. Incluir token de cancelación consultable desde el hilo principal.
- [x] **Hecho cuando:** `python -c "from controllers.gui_controller import GUIController; print('Despachador FIFO cargado')"` se ejecute con salida 0.

---

### Tarea 23: Integración de búsqueda asíncrona en el controlador
- **Archivo:** `controllers/gui_controller.py`
- **Requisitos cubiertos:** RF-03, RF-08
- **Descripción:** Implementar `buscar_por_nombre(termino: str)` ejecutado en hilo secundario para no congelar la UI. Invoca al resolver con límite de 5 resultados, actualiza la vista con `show_search_results` en éxito, o despliega modal en caso de fallo de red o resultado vacío. Gestionar el indicador visual de consulta (inicio/fin).
- [x] **Hecho cuando:** `python -c "from controllers.gui_controller import GUIController; assert hasattr(GUIController, 'buscar_por_nombre') or callable(getattr(GUIController, 'buscar_por_nombre', None)); print('Búsqueda asíncrona integrada')"` se ejecute con salida 0.

---

## Fase G — Bootstrap unificado y cero regresiones

### Tarea 24: Modificación del punto de entrada `main.py` para modo dual
- **Archivo:** `main.py`
- **Requisitos cubiertos:** RF-01, RNF-02
- **Descripción:** Modificar `main.py` para soportar modo dual: si se reciben argumentos de terminal (query, URL, `--limit`, etc.), despacha la ejecución CLI con `TerminalView` + `DownloadController` (sin regresiones). Si no se pasan argumentos o se usa `--gui`, arranca la aplicación Flet instanciando `FletView` + `GUIController`. Mantener el bootstrap bajo 50 líneas.
- [x] **Hecho cuando:** `python main.py -h` imprima la ayuda sin errores, y `python -c "import main; print('main.py modo dual verificado')"` se ejecute sin errores.

---

### Tarea 25: Verificación de cero regresiones en la suite completa de terminal
- **Archivos:** Todos los `tests/test_*.py` existentes
- **Requisitos cubiertos:** Criterio Finalización 9
- **Descripción:** Ejecutar la suite completa de pruebas automatizadas preexistentes (`test_controller.py`, `test_terminal_view.py`, `test_view_interface.py`, `test_events.py`, `test_downloader_events.py`, `test_platform_validator.py`, `test_validator.py`, `test_resolver.py`, `test_file_manager.py`, `test_format_validator.py`, `test_main_orchestration.py`, etc.) para asegurar que ningún módulo existente fue afectado por las modificaciones o adiciones.
- [x] **Hecho cuando:** `pytest tests/ -v --tb=short` pase al 100% sin ningún fallo ni warning en los tests preexistentes.

---

## Fase H — Pruebas GUI y documentación final

### Tarea 26: Pruebas unitarias headless del adaptador `FletView`
- **Archivo:** `tests/test_gui_adapter.py`
- **Requisitos cubiertos:** RF-01, RF-08, RNF-04, RNF-07
- **Descripción:** Crear `tests/test_gui_adapter.py` con al menos 3 pruebas ejecutables sin ventana gráfica: (1) validación estructural de que `FletView` implementa todos los métodos de `ViewInterface`, (2) emisión de `ProgressEvent` a la vista simulada en memoria verificando actualización de variables reactivas internas sin bucle visual, (3) inspección de literales de strings en las vistas confirmando ausencia de mensajes en inglés hacia el usuario.
- [x] **Hecho cuando:** `pytest tests/test_gui_adapter.py -v` ejecute al menos 3 pruebas y todas pasen al 100%.

---

### Tarea 27: Pruebas unitarias del analizador de enlaces mixtos
- **Archivo:** `tests/test_url_cleaner.py`
- **Requisitos cubiertos:** RF-02, Caso Límite 5
- **Descripción:** Crear `tests/test_url_cleaner.py` con al menos 3 pruebas: (1) poda automática de `watch?v=abc&list=RDabc` devolviendo solo `watch?v=abc` con `fue_podada=True`, (2) playlist genuina `playlist?list=PL...` no alterada con `fue_podada=False`, (3) video individual sin lista permanece intacto con `fue_podada=False`.
- [x] **Hecho cuando:** `pytest tests/test_url_cleaner.py -v` ejecute al menos 3 pruebas y todas pasen al 100%.

---

### Tarea 28: Actualización de `AGENTS.md` y bitácora final en `MEMORY.md`
- **Archivos:** `AGENTS.md`, `MEMORY.md`
- **Requisitos cubiertos:** Criterio Finalización 2
- **Descripción:** Actualizar `AGENTS.md` reflejando: coexistencia de modo terminal y modo gráfico, estructura del paquete `ui/gui/` (con `theme.py`, `flet_view.py` y las 5 vistas), `controllers/gui_controller.py`, `core/queue_manager.py`, los nuevos archivos de test y los comandos de ejecución (`python main.py` para GUI, `python main.py "query"` para CLI). Registrar decisiones y aprendizajes en `MEMORY.md`.
- [x] **Hecho cuando:** `Select-String -Path AGENTS.md -Pattern 'gui_controller'` devuelva coincidencia, y `Select-String -Path AGENTS.md -Pattern 'flet_view'` devuelva coincidencia.

---

### Tarea 29: Verificación global de la suite completa y sintaxis de módulos
- **Archivos:** Todos
- **Requisitos cubiertos:** Criterio Finalización 9, RNF-07
- **Descripción:** Ejecutar la suite completa de pruebas automatizadas (preexistentes + nuevas) para constatar cero regresiones y cobertura total de los RF. Verificar la carga sintáctica de todos los módulos nuevos y modificados.
- [x] **Hecho cuando:** `pytest tests/ -v` pase al 100% en todas las suites (superando 70 tests unitarios en total), y `python -c "import main, config, ui.terminal_view, ui.gui.flet_view, controllers.download_controller, controllers.gui_controller, core.queue_manager, utils.platform_validator, utils.file_manager; print('Todos los módulos cargados exitosamente')"` se ejecute sin errores.

---

## Resumen del grafo de dependencias

```
Tarea 1 (Constitución)
  └─► Tarea 2 (QueueItem DTOs)
       └─► Tarea 3 (Funciones FIFO)
            └─► Tarea 4 (Tests FIFO)
  └─► Tarea 5 (Colisiones de nombres)
       └─► Tarea 6 (Escaneo biblioteca)
            └─► Tarea 7 (Tests colisiones)
  └─► Tarea 8 (ViewInterface ampliada)
       └─► Tarea 9 (Tokens Figma)
            └─► Tarea 10 (Sidebar)
                 └─► Tarea 11 (Ventana principal FletView)
                      ├─► Tarea 12 (Home: enlace y pegado)
                      │    └─► Tarea 13 (Home: validación y recientes)
                      ├─► Tarea 14 (Búsqueda: 5 resultados)
                      └─► Tarea 15 (Opciones: formato y encolado)
                           ├─► Tarea 16 (Descargas: progreso activo)
                           │    └─► Tarea 17 (Descargas: cola visual FIFO)
                           │         └─► Tarea 18 (Descargas: éxito)
                           └─► Tarea 19 (Archivos: biblioteca)
       └─► Tarea 20 (Modales de error)
            └─► Tarea 21 (GUIController: base)
                 └─► Tarea 22 (Despachador FIFO async)
                      └─► Tarea 23 (Búsqueda asíncrona)
                           └─► Tarea 24 (main.py modo dual)
                                └─► Tarea 25 (Cero regresiones terminal)
                                     └─► Tarea 26 (Tests headless GUI)
                                          └─► Tarea 27 (Tests URL cleaner)
                                               └─► Tarea 28 (AGENTS.md + MEMORY.md)
                                                    └─► Tarea 29 (Verificación global)
```
