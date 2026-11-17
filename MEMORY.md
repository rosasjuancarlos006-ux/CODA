# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: QA Testing - Fase 3 / Tarea 3.4 completada (Ciclo de vida, cancelación activa con purga y prevent_close).
- **Funcionalidades**:
  - Arquitectura MVC estricta con contrato formal `ViewInterface`.
  - Capa de presentación gráfica modular con `flet>=0.21.0` en `ui/gui/` y modo terminal preexistente con `rich`.
  - Cola FIFO desacoplada (`core/queue_manager.py`) gestionada por `controllers/gui_controller.py` en hilo daemon.
  - Saneamiento y poda automática de mixes (`utils/validator.py` con `clean_mixed_url`).
  - Búsqueda asíncrona de 5 mejores resultados (`core/resolver.py`).
  - Resolución incremental de colisiones y escaneo de biblioteca local (`utils/file_manager.py`).
  - Entrada dual unificada (`main.py`) para ejecución GUI o CLI sin regresiones.
  - Throttling inteligente de eventos de progreso (100 ms) en FletView protegiendo renderizado de alta frecuencia.
  - Intercepción segura de cierre de ventana (`prevent_close`) con confirmación pedagógica y purga de temporales.
  - Suite de pruebas unitarias automatizadas con `pytest` pasando al 100% (238 tests en total).

## Decisiones clave (y por qué)
- **Flet 1.1.2 API adjustments**: Usar `ft.FilledButton` (en vez del obsoleto `ElevatedButton`), constructores capitalizados (`ft.Padding.only`, `ft.BorderRadius.all`) y `ft.Window` con `prevent_close=True` para intercepción limpia de cierre.
- **Protocol ViewInterface desacoplado**: La GUI y la CLI satisfacen el mismo contrato formal de presentación sin dependencias cruzadas.
- **Gestor de cola FIFO puro**: Operaciones inmutables en memoria con protección de tareas `ACTIVE` y purga de temporales ante cancelaciones.
- **Protección estricta de biblioteca**: Escaneo de solo lectura en `downloads/` y apertura en explorador nativo sin mutación de archivos.
- **Concurrencia FIFO blindada**: Pruebas multihilo simultáneas verificaron que `_lock` previene colisiones en encolado y garantiza ejecución estrictamente secuencial de tareas activas.

## Aprendizajes y errores a evitar
- **Controles no montados en Flet**: Invocar `control.update()` antes de agregar a la página lanza `RuntimeError`; encapsulado en `_safe_update()`.
- **Intercepción de eventos de ventana**: Manejar `window.on_event` confirmando si existen descargas activas antes de destruir la ventana.
- **Degradación visual elegante**: Cuando `ProgressEvent` no reporta velocidad o porcentaje, conmutar a `ProgressBar(value=None)` y spinner sin abortar la descarga.
- **Navegación vs Notificación no invasiva**: Encolar sin tareas activas redirige de inmediato a descargas; encolar con descarga activa emite un toast sin forzar cambio de panel.
