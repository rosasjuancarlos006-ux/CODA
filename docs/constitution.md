# Constitución de Coda

1. **Stack mínimo.** Solo 4 dependencias de producción (yt-dlp, mutagen, requests, rich) + FFmpeg externo. Toda nueva dependencia requiere justificación escrita en MEMORY.md.
2. **La spec manda.** Si AGENTS.md dice cómo funciona algo, el código debe reflejarlo exactamente. Cambiar el comportamiento implica actualizar AGENTS.md primero.
3. **Lógica e interfaz separadas.** `core/` y `metadata/` nunca importan de `ui/`. La interfaz puede reemplazarse sin tocar una línea de la lógica de descarga.
4. **Tests sin instalar nada extra.** Las pruebas en `tests/` cubren módulos puros (`utils/`) y la lógica de coordinación del controlador utilizando vistas simuladas en memoria (*mocks*/*fakes* con la biblioteca estándar), sin dependencias externas de prueba. Se ejecutan con `pytest tests/ -v` y deben pasar al 100% antes de cualquier merge.
5. **Los archivos del usuario son sagrados.** Coda solo escribe dentro de `downloads/` y `app.log`. Nunca modifica, lee ni elimina archivos fuera de esas rutas.
6. **Español al usuario, inglés al código.** Mensajes, menús y errores en pantalla van en español. Nombres de funciones, variables y logs van en inglés.
