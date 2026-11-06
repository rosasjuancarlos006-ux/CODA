# MEMORY.md — Diario de Estudio
Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no aporte.

## Estado actual
- **Versión**: Fase 7 (Soporte multiplataforma: YouTube y YouTube Music).
- **Funcionalidades**:
  - Selector de plataforma interactivo (`[1] YouTube`, `[2] YouTube Music`) con alias y reintentos.
  - Inferencia automática de plataforma por dominio en ejecuciones CLI directas sin fricción.
  - Búsqueda contextual orientada para YouTube Music (`ytsearch1:{query} Audio Oficial`).
  - Saneamiento automático de enlaces de video con radio/mix (`&list=RD...`) vía `clean_video_url`.
  - Auto-adaptación pedagógica con advertencia visual ante discrepancias entre la plataforma y el enlace.
  - Selección interactiva de formato de audio (`mp3`, `m4a`, `opus`) con degradación elegante.
  - Suite de 43 pruebas unitarias automatizadas con `pytest` pasando al 100%.

## Decisiones (y por qué)
- **Módulo puro `utils/platform_validator.py`**: Aislamiento de reglas de plataforma y discrepancia (Principio 3), testeable sin I/O (Principio 4).
- **Poda de mixes en tracks individuales**: Previene que `yt-dlp` procese playlists infinitas accidentales ante URLs `watch?v=...&list=RD...`.
- **Enriquecimiento contextual en búsquedas**: Prioriza versiones oficiales de estudio en YouTube Music sin agregar dependencias externas (Principio 1).
- **Auto-adaptación con feedback**: No bloquea al usuario si pega un enlace cruzado; ajusta la plataforma y emite advertencia pedagógica.

## Aprendizajes y errores a evitar
- **Colapso de espacios en alias**: Normalizar espacios intermedios múltiples (`"youtube   music"` -> `"youtube music"`) para robustez de entrada.
- **Prioridad de tracks sobre mixes**: Clasificar siempre URLs con `/watch?v=` como `video` incluso si contienen parámetro `&list=`.

## Próximos pasos
- Selector interactivo de calidad/bitrate (128, 192, 256, 320 kbps).
- Posible soporte nativo de metadatos para contenedores MP4/M4A.
