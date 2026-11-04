# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: Fase 5 (GitHub-Ready / Prototipo Completo).
- **Funcionalidades**:
  - UX enriquecida en terminal con Rich (banner ASCII, paneles, tablas y progress bars).
  - Descarga individual y playlists en MP3 (192 kbps) con carátulas APIC y metadatos ID3v2.
  - Logging integral persistiendo en `app.log`.
  - Manejo de excepciones exhaustivo en cada capa (red, YouTube, tags, interacción).
  - Suite de pruebas unitarias con `pytest` para validación de URLs y sanitización de rutas.
  - Repositorio estructurado para GitHub: `README.md`, `.gitignore`, `LICENSE` (MIT) y `requirements.txt`.

## Decisiones (y por qué)
- **Exclusión de `bin/` y `downloads/` en Git**: Binarios pesados (~340 MB) y archivos MP3 se ignoran en `.gitignore` para mantener un repo ligero; la instalación de FFmpeg se documentó en el `README.md`.
- **Logging centralizado en `app.log`**: Evita contaminar la interfaz gráfica de Rich y permite auditar fallos y peticiones.
- **Suite de pruebas**: `tests/` con 9 pruebas cubriendo regex de YouTube, detección de listas y sanitización de caracteres Windows.

## Aprendizajes y errores a evitar
- **Robustez ante interrupciones**: Capturar `KeyboardInterrupt` limpiamente en la CLI para evitar tracebacks feos al pulsar Ctrl+C.
- **Trazabilidad sin ruido visual**: El modo silencioso de `yt-dlp` combinado con `app.log` permite una terminal limpia sin perder diagnóstico técnico.

## Próximos pasos
- Publicación en repositorio remoto GitHub (`rosasjuancarlos006-ux/youtube-music-downloader`).
- Posible soporte opcional para otros formatos de audio (FLAC/AAC) en versiones posteriores.
