# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: Fase 8 (Arquitectura Modelo-Vista-Controlador - MVC).
- **Funcionalidades**:
  - Desacoplamiento total de la vista mediante contrato abstracto `ViewInterface` (`typing.Protocol`).
  - Implementación concreta en terminal con Rich (`ui/terminal_view.py`) con degradación visual ante streams dinámicos.
  - Emisión de eventos agnósticos inmutables (`core/events.py`) desde el motor de descarga (`ProgressEvent`, `DownloadPhase`).
  - Bucle interactivo resiliente en `DownloadController` tolerante a fallos recuperables y entradas vacías.
  - Cancelación limpia (Ctrl+C) con retorno seguro al menú y supresión de archivos parciales huérfanos.
  - Consulta y formateo de biblioteca de descargas filtrando formatos soportados (`.mp3`, `.m4a`, `.opus`).
  - Bootstrap minimalista en `main.py` (< 35 líneas) con inyección de dependencias.
  - Enmienda a la Regla 4 de `docs/constitution.md` para testing de controladores con *mocks* en memoria.
  - Suite de 86 pruebas unitarias automatizadas con `pytest` pasando al 100%.

## Decisiones (y por qué)
- **Protocol en lugar de ABC para ViewInterface**: Permite duck typing estático y creación instantánea de `FakeView` en tests sin acoplar jerarquías de herencia.
- **DTOs ProgressEvent inmutables**: El modelo (`core/downloader.py`) emite datos primitivos y nunca importa módulos de UI.
- **Limpieza contextual de temporales**: Se eliminan archivos huérfanos si la operación es cancelada por el usuario, pero se conserva el audio si solo fallan metadatos.

## Aprendizajes y errores a evitar
- **Validación de strings de consola**: Siempre aplicar `.strip()` antes de comprobar si la entrada está vacía (`stripped = raw_input.strip() if raw_input else ""`).
- **Bootstrap libre de lógica**: `main.py` solo debe orquestar el inicio del controlador y la vista correspondiente.

## Próximos pasos
- Implementación de interfaz gráfica de escritorio alternativa (Flet GUI) consumiendo `ViewInterface`.
- Selector interactivo de calidad/bitrate (128, 192, 256, 320 kbps).
