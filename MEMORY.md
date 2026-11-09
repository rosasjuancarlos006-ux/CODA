# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: Fase 7.1 (Resiliencia de red, timeouts en yt-dlp e integridad ID3/carátulas).
- **Funcionalidades**:
  - Selector de plataforma interactivo (`[1] YouTube`, `[2] YouTube Music`) con alias y reintentos.
  - Inferencia automática de plataforma por dominio en ejecuciones CLI directas sin fricción.
  - Búsqueda contextual orientada para YouTube Music (`ytsearch1:{query} Audio Oficial`).
  - Saneamiento automático de enlaces de video con radio/mix (`&list=RD...`) vía `clean_video_url`.
  - Auto-adaptación pedagógica con advertencia visual ante discrepancias entre plataforma y enlace.
  - Timeouts de red (`socket_timeout: 15`, `retries: 3`, `fragment_retries: 3`) en `yt-dlp` para evitar cuelgues indefinidos.
  - Integridad en escritura de tags EasyID3 (retorna `False` ante fallos sin reportar falsos positivos).
  - Transcodificación automática de carátulas WebP a JPEG vía Pillow/FFmpeg con fallback sin corromper tags APIC.
  - Protección de timestamps en fallback de archivos evitando inyectar metadatos en canciones antiguas.
  - Suite de 48 pruebas unitarias automatizadas con `pytest` pasando al 100%.

## Decisiones (y por qué)
- **Timeouts defensivos en yt-dlp**: Resuelve bloqueos silenciosos en streams lentos o corte de sockets.
- **Validación estricta de tags ID3**: Si fallan los campos de texto esenciales, se informa error para evitar falsos éxitos en UI.
- **Transcodificación a JPEG vía FFmpeg local**: Resuelve carátulas WebP de YouTube Music sin requerir obligatoriamente Pillow en requirements.
- **Aislamiento de timestamps en downloads**: `st_mtime >= download_start_time` evita contaminar pistas previas si la descarga actual no escribe archivo.

## Aprendizajes y errores a evitar
- **Evitar circular imports**: `metadata.writer` y `core.downloader` deben desacoplar utilidades binarias como `find_ffmpeg`.
- **EasyID3 try/except**: Nunca silenciar errores en tags de texto devolviendo `True` al final de la función.

## Próximos pasos
- Selector interactivo de calidad/bitrate (128, 192, 256, 320 kbps).
- Soporte nativo de metadatos en contenedores MP4/M4A.
