# Especificación de Requisitos — Selección de Formato de Audio

## Contexto y Objetivo
Actualmente, Coda descarga y procesa streams de audio exclusivamente en formato MP3. Sin embargo, los usuarios cuentan con distintas necesidades de compatibilidad, rendimiento y calidad de compresión (por ejemplo, `m4a` para el ecosistema Apple o `opus` para máxima fidelidad acústica a menor tamaño de archivo).

El objetivo de esta funcionalidad es permitir al usuario elegir dinámicamente el formato de audio de salida (`mp3`, `m4a` u `opus`) para cada operación de descarga (tanto pistas individuales como playlists completas). La experiencia debe ser guiada, resiliente a errores tipográficos, compatible con la Constitución de Coda y tolerante a fallos en la inyección de metadatos o portadas según el formato.

---

## Usuarios
- **Usuario general / Casual**: Busca descargar canciones de forma inmediata aceptando la opción predeterminada (`mp3`) con una pulsación de tecla.
- **Usuario con preferencias de audio**: Desea seleccionar conscientemente formatos modernos (`m4a` u `opus`) para sus dispositivos o bibliotecas personales.

---

## Historias de Usuario

### HU-01: Selección de formato para canción individual o búsqueda
- **Como** usuario de Coda,
- **Quiero** que el sistema me consulte qué formato deseo (`mp3`, `m4a`, `opus`) antes de comenzar la descarga de una canción o búsqueda,
- **Para** obtener el archivo final en el contenedor de audio de mi preferencia.

### HU-02: Selección de formato unificada para playlist completa
- **Como** usuario de Coda,
- **Quiero** definir el formato una sola vez para toda una playlist, con una advertencia visible de que aplicará a todas sus pistas,
- **Para** asegurar una descarga uniforme de la colección sin responder preguntas repetitivas pista por pista.

### HU-03: Confirmación rápida por defecto
- **Como** usuario que busca rapidez,
- **Quiero** pulsar la tecla Enter (o ingresar solo espacios) para aceptar automáticamente `mp3`,
- **Para** continuar sin fricción cuando no requiero un formato especial.

---

## Requisitos Funcionales (RF)

### RF-01: Momento y despliegue del menú de selección
- **Descripción**: El sistema debe solicitar interactivamente el formato de audio justo antes de la fase de descarga y conversión.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* se inicie una descarga de canción individual o búsqueda (por menú o por argumento directo en terminal), *el sistema debe* solicitar el formato de audio antes de transferir o convertir el audio.
  - *Cuando* se inicie la descarga de una playlist, *el sistema debe* solicitar primero la cantidad de canciones a descargar (límite) y, acto seguido, solicitar el formato de audio advirtiendo explícitamente: `El formato seleccionado aplicará a todas las canciones de la playlist`.
  - *Cuando* el sistema presente el prompt de selección, *el sistema debe* listar visualmente las opciones `[mp3, m4a, opus]` destacando `mp3` como valor por defecto (ejemplo: `Formato de audio [mp3/m4a/opus] (Enter = mp3): `).

### RF-02: Normalización de entrada y selección por defecto
- **Descripción**: La entrada debe limpiarse de espacios laterales y homologarse a minúsculas antes de la validación.
- **Criterios de Aceptación (EARS)**:
  - *Si* la entrada del usuario queda vacía tras eliminar espacios en blanco (pulsación de tecla Enter o solo espacios `   `), *el sistema debe* asignar automáticamente `mp3` como el formato seleccionado.
  - *Si* el usuario ingresa variantes con mayúsculas o espacios circundantes (ejemplos: ` MP3 `, `OpUs`, `m4A`), *el sistema debe* normalizarlas a minúsculas y aceptarlas como válidas.

### RF-03: Manejo de entradas inválidas y ciclo de reintento
- **Descripción**: Bloquear entradas no admitidas sin abortar la operación ni atrapar indefinidamente al usuario.
- **Criterios de Aceptación (EARS)**:
  - *Si* el usuario ingresa un valor distinto de `mp3`, `m4a` u `opus` (incluyendo cadenas largas o caracteres extraños), *el sistema debe* mostrar un mensaje de advertencia indicando que la opción no es válida, recordar que los formatos disponibles son `mp3`, `m4a` y `opus`, y volver a solicitar el formato.
  - *Mientras* el usuario continúe ingresando opciones inválidas, *el sistema debe* permitir hasta 3 reintentos consecutivos.
  - *Si* el usuario supera los 3 intentos fallidos consecutivos, *el sistema debe* notificar que se aplicará la opción predeterminada y seleccionar automáticamente `mp3`.

### RF-04: Conversión y nombrado en el formato elegido
- **Descripción**: El motor de conversión debe generar el contenedor y códec correspondiente.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* la descarga concluya exitosamente, *el sistema debe* entregar el archivo en `downloads/` con la extensión correspondiente (`.mp3`, `.m4a` o `.opus`).

### RF-05: Metadatos y carátula con degradación elegante
- **Descripción**: Intentar inyectar tags y portada respetando las limitaciones técnicas de cada contenedor de audio sin perder el archivo.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el archivo de audio haya sido generado, *el sistema debe* intentar incrustar título, artista y carátula frontal.
  - *Si* el formato no admite incrustación de carátula o etiquetas con las herramientas actuales del proyecto, *el sistema debe* preservar el archivo de audio intacto y emitir una advertencia visible informando que el formato no soporta dicha incrustación de metadatos o carátula.
  - *Si* la inyección de metadatos o carátula falla debido a un error técnico en tiempo de ejecución (ejemplo: portada corrupta o error de I/O), *el sistema debe* preservar el archivo de audio descargado y emitir una advertencia visible reportando el fallo técnico sin interrumpir el flujo.

---

## Requisitos No Funcionales (RNF)

- **RNF-01 (Constitución — Stack mínimo)**: Cumplir estrictamente el Principio 1 de `docs/constitution.md`. No se permite incorporar dependencias de producción adicionales en `requirements.txt`.
- **RNF-02 (Constitución — Separación UI/Core)**: Cumplir con el Principio 3 de `docs/constitution.md`. La función o utilidad de validación y normalización del formato debe residir en `utils/` como función pura, desacoplada de la interfaz gráfica y de la lógica de descarga.
- **RNF-03 (Constitución — Idiomas)**: Cumplir con el Principio 6 de `docs/constitution.md`:
  - Interfaz de usuario (prompts, advertencias, tablas): **Español**.
  - Código, nombres de variables, funciones y registros en `app.log`: **Inglés**.
- **RNF-04 (No persistencia)**: La elección de formato es volátil por operación. No debe modificar archivos en disco ni alterar variables globales persistentes.
- **RNF-05 (Trazabilidad y Niveles de Log)**:
  - La selección efectiva del formato se registrará como `INFO` en `app.log` (ejemplo: `Selected audio format: opus`).
  - Cada entrada inválida reintentada se registrará como `DEBUG` (ejemplo: `Invalid format option entered: 'flac'`).
  - La degradación por falta de soporte de metadatos o fallos de inyección se registrará como `WARNING` (ejemplo: `Cover art embedding not supported for format: opus`).

---

## Casos Límite

1. **Entrada vacía o sólo espacios (`""`, `"   "`)**: Se clasifica automáticamente como selección de `mp3` sin activar reintento.
2. **Entrada con mayúsculas y espacios (`"  M4A  "`)**: Se limpia y se valida exitosamente como `m4a`.
3. **Entradas excesivamente largas o pegadas por error**: Cadenas de más de 20 caracteres se consideran entradas inválidas de inmediato sin desbordar la interfaz.
4. **Interrupción por teclado (`Ctrl+C`) en el prompt de formato**: El sistema debe capturar `KeyboardInterrupt` limpiamente, cancelando la operación actual y volviendo al menú principal (o saliendo limpiamente en modo CLI) sin tracebacks.
5. **Fallo de descarga posterior a la selección**: Si no hay conexión o el video es privado, los mensajes de error existentes en Coda se despliegan normalmente; la elección de formato no interfiere con el diagnóstico de red o privacidad.
6. **Fallo parcial en playlists**: Si una pista dentro de una playlist falla en descarga o conversión, se registra en la bitácora y la tabla final reporta dicha pista como fallida, mientras las restantes se continúan procesando en el formato elegido.

---

## Fuera de Alcance

- Selección personalizada de tasa de bits (bitrate) por formato.
- Soporte para formatos sin compresión o sin pérdida (WAV, FLAC, ALAC).
- Modos silenciosos o banderas CLI para preconfigurar el formato (la selección se mantiene interactiva y guiada).
- Conversión retrospectiva de archivos existentes en la carpeta de descargas.

---

## Criterios de Finalización

- [ ] Existe una función pura en `utils/` encargada de validar y normalizar el formato de audio seleccionado.
- [ ] La selección interactiva se ejecuta antes de cualquier descarga (tanto individual como playlist, en modo interactivo y CLI).
- [ ] En playlists, la pregunta de formato ocurre después de consultar el límite de pistas y advierte que aplicará a todas las canciones.
- [ ] Presionar Enter o ingresar solo espacios selecciona `mp3` de forma inmediata.
- [ ] Entradas inválidas despliegan advertencia en español, recuerdan `[mp3, m4a, opus]` y permiten hasta 3 reintentos antes de seleccionar `mp3` por defecto.
- [ ] Los archivos de audio resultantes se generan con la extensión y códec correspondiente (`.mp3`, `.m4a`, `.opus`).
- [ ] Los fallos o limitaciones de metadatos no destruyen el archivo descargado y muestran advertencias amigables al usuario.
- [ ] El archivo `app.log` registra la selección en `INFO`, los reintentos en `DEBUG` y las omisiones de metadatos en `WARNING`, todo en inglés.
- [ ] Nuevas pruebas unitarias en `tests/` cubren la función pura de validación/normalización de formato al 100%, ejecutándose con `pytest tests/ -v` sin dependencias adicionales (Principio 4).

---

## Dudas Abiertas

- *Ninguna duda abierta identificada.* Todos los puntos de ambigüedad, casos límite y compatibilidad con la Constitución han quedado formalmente fijados.
