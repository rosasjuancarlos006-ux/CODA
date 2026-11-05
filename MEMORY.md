# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: Fase 6 (Soporte multiformato dinámico: MP3, M4A, OPUS).
- **Funcionalidades**:
  - Selección interactiva de formato (`mp3`, `m4a`, `opus`) por operación con límite de 3 reintentos y fallback a `mp3`.
  - Configuración unificada para playlists con advertencia visible.
  - Conversión dinámica mediante postprocesador de `yt-dlp` y extracción de audio vía FFmpeg.
  - Degradación elegante de metadatos: los formatos sin soporte de tags se conservan intactos sin interrumpir el flujo.
  - UX en terminal con Rich y tabla de biblioteca de descargas multiformato.
  - Suite de 18 pruebas unitarias con `pytest` pasando al 100%.

## Decisiones (y por qué)
- **Función pura en `utils/format_validator.py`**: Separación de lógica e interfaz (Principio 3) permitiendo testeo unitario exhaustivo sin mocks de consola (Principio 4).
- **Degradación elegante en metadatos**: Formatos distintos de MP3 omiten la inyección de tags emitiendo un warning sin crashear ni alterar el archivo de audio.
- **Solicitud interactiva en CLI directo**: Cuando se pasa argumento por CLI, se despliega el prompt de formato antes de procesar para garantizar control de usuario uniforme.

## Aprendizajes y errores a evitar
- **Normalización de formatos**: Convertir siempre a minúsculas y limpiar espacios laterales antes de verificar membresía (`.strip().lower()`).
- **Resiliencia ante entradas inválidas**: Limitar a 3 reintentos para evitar atrapar al usuario en bucles infinitos ante errores tipográficos reiterados.

## Próximos pasos
- Selector interactivo de calidad/bitrate (128, 192, 256, 320 kbps).
- Posible soporte nativo de metadatos para MP4/M4A usando herramientas del stack.
