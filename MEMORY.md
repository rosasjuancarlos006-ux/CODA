# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: QA Testing & Frontend Design Studio — Flet GUI Desktop/Web optimizado.
- **Funcionalidades**:
  - Arquitectura MVC estricta con contrato formal `ViewInterface`.
  - Capa de presentación gráfica desacoplada con Flet en `ui/gui/` y modo terminal con `rich`.
  - Diseño visual profesional: paleta Studio Dark (`#0E0F12`), tipografía de sistema moderna, inputs fluidos sin bordes redundantes (`ft.NoInputBorder()`) y búsqueda con tecla Enter.
  - Cola FIFO desacoplada (`core/queue_manager.py`) en hilo daemon con protección de tareas activas.
  - Saneamiento de mixes (`clean_mixed_url`), búsqueda asíncrona de top 5 y transcodificación multiformato (MP3/M4A/OPUS).
  - Cancelación activa con purga atómica de temporales e intercepción de cierre de ventana (`prevent_close`).
  - Suite de pruebas unitarias automatizadas con `pytest` pasando al 100% (238 tests).

## Decisiones (y por qué)
- **Flet 1.1.2 Modern API & Web**: Eliminación de `InputBorder.NONE` obsoleto en favor de `NoInputBorder()`, compatibilidad total de temas sin keyword no soportada `background` en `ColorScheme`.
- **Diseño Editorial Studio Dark**: Mayor separación tonal entre fondo (`#0E0F12`) y contenedores (`#16181D`), mejorando legibilidad y ergonomía en escritorio y navegador web.
- **Protocol ViewInterface desacoplado**: GUI y CLI implementan el mismo protocolo agnóstico a librerías concretas.
- **Concurrencia FIFO blindada**: Worker asíncrono con `_lock` garantizando ejecución estrictamente secuencial y cancelación limpia.

## Aprendizajes y errores a evitar
- **ColorScheme en Flet**: No pasar argumento `background` a `ft.ColorScheme`; el fondo de página se asigna vía `page.bgcolor`.
- **Flet deprecations**: Usar `ft.NoInputBorder()` para campos limpios integrados en contenedores con bordes estilizados.
- **Controles no montados**: Nunca invocar `.update()` directamente en componentes no montados; usar `_safe_update()`.

## Próximos pasos
- Empaquetado binario ejecutable (.exe / instalador de escritorio o despliegue web).
- Soporte para edición o personalización de tags ID3 manual previa a la descarga.
