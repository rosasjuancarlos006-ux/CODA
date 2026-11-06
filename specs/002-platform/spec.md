# Especificación de Requisitos — Soporte Multiplataforma (YouTube / YouTube Music)

## Contexto y Objetivo
Actualmente, Coda opera asumiendo el catálogo general de YouTube para resolver búsquedas y enlaces. Sin embargo, los usuarios que escuchan música en streaming frecuentemente utilizan enlaces específicos de **YouTube Music** (`https://music.youtube.com/...`), los cuales cuentan con diferencias de catálogo, metadatos orientados específicamente a pistas de audio/álbumes oficiales y variantes de enlaces (tracks y playlists).

El objetivo de esta funcionalidad es permitir al usuario seleccionar explícitamente la plataforma de origen deseada (**YouTube** o **YouTube Music**) en el flujo interactivo antes de ingresar su consulta o enlace. Esto orienta al usuario sobre el tipo de recurso que gestionará, adapta las búsquedas por texto al catálogo oficial de cada plataforma, valida enlaces con advertencias amigables en caso de discrepancias y auto-adapta la operación sin interrumpir el flujo. Además, en ejecuciones directas por terminal (CLI), el sistema detecta automáticamente la plataforma del enlace para minimizar la fricción.

---

## Usuarios
- **Usuario de YouTube general**: Busca canciones, remixes, versiones en vivo o videos musicales en el catálogo global de YouTube.
- **Usuario de YouTube Music**: Maneja enlaces de `music.youtube.com`, buscando versiones de estudio, álbumes oficiales y playlists curadas de la plataforma musical.

---

## Historias de Usuario

### HU-01: Selección interactiva previa de plataforma
- **Como** usuario de Coda en modo interactivo,
- **Quiero** poder elegir si mi búsqueda o descarga provendrá de "YouTube" o "YouTube Music" antes de ingresar el término o enlace,
- **Para** asegurar que la búsqueda consulte el catálogo adecuado y saber qué enlace espera el sistema.

### HU-02: Búsqueda específica por catálogo musical
- **Como** usuario que busca música por nombre o artista,
- **Quiero** que al elegir "YouTube Music", el motor de búsqueda priorice pistas del catálogo oficial de música en lugar de videos genéricos de YouTube,
- **Para** obtener la versión musical oficial con mejor estructura de títulos y metadatos.

### HU-03: Soporte para enlaces y playlists de YouTube Music
- **Como** usuario de YouTube Music,
- **Quiero** poder pegar enlaces directos de tracks (`music.youtube.com/watch?v=...`) o playlists (`music.youtube.com/playlist?list=...`),
- **Para** descargar mi música preferida directamente desde dicha plataforma con la misma experiencia y límites configurables.

### HU-04: Auto-adaptación ante discrepancia de enlace
- **Como** usuario que comete un error al seleccionar la plataforma o copiar el enlace,
- **Quiero** recibir una advertencia visual clara si el enlace pertenece a la otra plataforma pero que el sistema lo procese automáticamente sin bloquearme,
- **Para** no tener que cancelar la operación ni volver a empezar desde cero.

### HU-05: Detección transparente en modo CLI
- **Como** usuario que ejecuta Coda pasando argumentos directamente por terminal,
- **Quiero** que el sistema infiera automáticamente la plataforma a partir del dominio del enlace sin hacerme preguntas redundantes,
- **Para** obtener una descarga rápida y sin fricción.

---

## Requisitos Funcionales (RF)

### RF-01: Menú interactivo de selección de plataforma y normalización
- **Descripción**: El sistema debe solicitar la plataforma deseada en el modo interactivo antes de solicitar la URL o texto de búsqueda, con alta tolerancia a fallos en la entrada.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario inicie una descarga desde el menú interactivo, *el sistema debe* desplegar una consulta interactiva listando las opciones: `[1] YouTube` y `[2] YouTube Music`, indicando que `YouTube` es la opción por defecto.
  - *Si* el usuario presiona Enter o ingresa solo espacios en blanco, *el sistema debe* seleccionar `YouTube` por defecto.
  - *Si* el usuario ingresa alias normalizables (ignorando mayúsculas y espacios extremos):
    - Para YouTube: `1`, `youtube`, `yt`.
    - Para YouTube Music: `2`, `youtube music`, `music`, `ytmusic`.
    *el sistema debe* aceptar la opción y continuar el flujo.
  - *Si* el usuario ingresa un valor no reconocido, *el sistema debe* notificar el error, recordar las opciones válidas y permitir hasta 3 reintentos antes de asignar `YouTube` por defecto.

### RF-02: Detección automática en ejecuciones CLI directas
- **Descripción**: Manejo sin preguntas de plataforma cuando se invoca Coda con argumentos directos en terminal.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario ejecute la aplicación pasando un argumento directo (`python main.py <query>`):
    - *Si* la consulta es una URL con dominio de YouTube Music (`music.youtube.com`), *el sistema debe* asignar automáticamente la plataforma como `YouTube Music`.
    - *En cualquier otro caso* (URL de YouTube estándar o texto de búsqueda), *el sistema debe* asignar automáticamente la plataforma como `YouTube`.
  - *El sistema debe* proceder directamente al paso siguiente (consulta de formato de audio o límite de playlist) sin desplegar el prompt de selección de plataforma.

### RF-03: Soporte y clasificación de URLs de YouTube Music
- **Descripción**: El validador en `utils/` debe reconocer tracks individuales y playlists de `music.youtube.com`.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* la entrada sea una URL de playlist pura (`https://music.youtube.com/playlist?list=...`), *el sistema debe* clasificarla como playlist de YouTube Music.
  - *Cuando* la entrada sea una URL de video (`https://music.youtube.com/watch?v=...`), incluso si incluye parámetros adicionales de lista o radio (ejemplo: `&list=RD...`), *el sistema debe* priorizarla y clasificarla como pista individual de YouTube Music.

### RF-04: Búsqueda orientada por catálogo
- **Descripción**: Resolver la consulta según la plataforma seleccionada.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* la entrada sea texto libre y la plataforma sea `YouTube`, *el sistema debe* anteponer el prefijo de búsqueda general de YouTube (`ytsearch1:`).
  - *Cuando* la entrada sea texto libre y la plataforma sea `YouTube Music`, *el sistema debe* resolver la búsqueda orientándola a pistas de YouTube Music (prefijo de búsqueda musical o query contextual).

### RF-05: Advertencia pedagógica y auto-adaptación de enlaces cruzados
- **Descripción**: Tolerancia ante discrepancias entre la plataforma elegida y el enlace suministrado.
- **Criterios de Aceptación (EARS)**:
  - *Si* el usuario seleccionó `YouTube Music` pero ingresa una URL con dominio de YouTube general (`youtube.com` o `youtu.be`), *el sistema debe* emitir una advertencia visible en español indicando la discrepancia, auto-adaptar la plataforma a `YouTube` y continuar la descarga sin abortar la operación.
  - *Si* el usuario seleccionó `YouTube` pero ingresa una URL con dominio de YouTube Music (`music.youtube.com`), *el sistema debe* emitir una advertencia visible en español indicando la discrepancia, auto-adaptar la plataforma a `YouTube Music` y continuar la descarga sin abortar la operación.

### RF-06: Orden lineal del flujo de interacción
- **Descripción**: La secuencia de interacción debe seguir un orden predecible y coherente.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* se ejecute una descarga interactiva, *el sistema debe* ejecutar estrictamente el siguiente orden cronológico:
    1. Selección de plataforma (`YouTube` o `YouTube Music`).
    2. Entrada de URL o término de búsqueda (con auto-adaptación y advertencia si aplica).
    3. Configuración de límite de pistas (únicamente si se detectó una playlist).
    4. Selección de formato de audio (`mp3`, `m4a`, `opus`).
    5. Procesamiento y descarga.

---

## Requisitos No Funcionales (RNF)

- **RNF-01 (Constitución — Stack mínimo)**: Cumplir estrictamente el Principio 1 de `docs/constitution.md`. No se permite incorporar dependencias de producción adicionales en `requirements.txt`.
- **RNF-02 (Constitución — Separación Lógica/UI)**: La detección de plataforma, clasificación de URLs y resolución de discrepancias deben residir como funciones puras en `utils/`, desacopladas de la interfaz y de la consola.
- **RNF-03 (Constitución — Idiomas)**: Cumplir con el Principio 6 de `docs/constitution.md`:
  - Interfaz de usuario (prompts, advertencias de auto-adaptación, mensajes de menú): **Español**.
  - Código, nombres de variables, funciones y bitácora en `app.log`: **Inglés**.
- **RNF-04 (No persistencia)**: La plataforma elegida es volátil por operación. No debe modificar archivos en disco ni alterar variables globales persistentes.
- **RNF-05 (Trazabilidad y Logging)**:
  - La selección efectiva de plataforma debe registrarse en `INFO` en `app.log` (ejemplo: `Selected platform: YouTube Music`).
  - Las discrepancias y auto-adaptaciones deben registrarse en `WARNING` en `app.log` (ejemplo: `Platform mismatch detected: URL belongs to YouTube Music. Auto-adapting.`).

---

## Casos Límite

1. **URLs con parámetros extraños (`si=...`, `feature=share`)**: El validador debe extraer limpiamente los IDs de video o lista ignorando parámetros de tracking.
2. **URLs de pistas con parámetro de mix/radio (`watch?v=...&list=RD...`)**: Se procesa exclusivamente la canción individual señalada en el parámetro `v=`, evitando descargar mixes infinitos accidentales.
3. **Subdominios con o sin `www`**: Se admiten indistintamente `music.youtube.com`, `www.music.youtube.com`, `youtube.com` y `www.youtube.com`.
4. **Interrupción por teclado (`Ctrl+C`) en el selector de plataforma**: El sistema captura la señal limpiamente y regresa al menú o finaliza sin tracebacks.
5. **Entrada de solo espacios en el selector**: Se interpreta de forma idéntica a presionar Enter (asigna `YouTube` por defecto).

---

## Fuera de Alcance

- Integración con Spotify (obtención de metadatos, resolución de enlaces de Spotify o enriquecimiento de tags con Spotify API). Queda postergado formalmente para la especificación `003-spotify`.
- Soporte para plataformas distintas de YouTube y YouTube Music (ej. SoundCloud, Deezer, Apple Music).
- Autenticación o inicio de sesión con cuentas de YouTube Music Premium.
- Descarga de letras sincronizadas de YouTube Music.

---

## Criterios de Finalización

- [x] Existe una función pura en `utils/` encargada de validar y normalizar la plataforma seleccionada (`1/yt/youtube` -> `youtube`, `2/music/ytmusic` -> `youtube_music`).
- [x] En modo interactivo, el menú de plataforma aparece como primer paso antes de solicitar el enlace/texto.
- [x] En modo CLI directo (`python main.py <query>`), la plataforma se auto-detecta por URL sin mostrar el prompt.
- [x] El validador en `utils/` reconoce y clasifica URLs de `music.youtube.com` (diferenciando playlists puras de tracks con mixes).
- [x] Pegar un enlace cruzado (ej. enlace de YouTube Music en modo YouTube) emite una advertencia en español y auto-adapta la operación sin abortar.
- [x] El flujo lineal sigue estrictamente: Plataforma -> Entrada -> Límite (si es playlist) -> Formato de audio.
- [x] Se registran los eventos de selección (`INFO`) y auto-adaptación (`WARNING`) en `app.log` en inglés.
- [x] Las pruebas unitarias en `tests/` cubren las nuevas funciones puras de validación de plataforma y URLs al 100%, ejecutándose con `pytest tests/ -v` sin dependencias adicionales.

---

## Dudas Abiertas

- *Ninguna duda abierta.* Todas las ambigüedades, orden cronológico y casos límite fueron resueltos en la sesión de clarificación.
