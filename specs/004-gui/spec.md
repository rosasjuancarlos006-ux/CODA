# Especificación de Requisitos — Interfaz Gráfica de Usuario (GUI)

## Contexto y Objetivo

Coda cuenta con una arquitectura desacoplada basada en el patrón Modelo-Vista-Controlador (MVC), donde la lógica de extracción de audio, resolución de plataformas y etiquetado de metadatos se encuentra aislada de la capa de presentación mediante un contrato formal de vista (`ViewInterface`). La implementación existente corresponde a una vista de terminal basada en Rich.

El objetivo de esta funcionalidad es desarrollar una interfaz gráfica de usuario (GUI) moderna, intuitiva y visualmente cuidada para Coda, implementando el contrato de presentación existente y reflejando fielmente el diseño y flujo visual especificado en el prototipo interactivo de Figma denominado **«CODA»**. Esta interfaz proporcionará a los usuarios una experiencia de escritorio fluida para explorar, buscar, configurar y descargar audio individual o listas de reproducción desde YouTube y YouTube Music, monitorear el progreso en tiempo real a través de una cola de trabajo interactiva y consultar los archivos descargados localmente, manteniendo una estricta separación de responsabilidades y respetando la Constitución del proyecto mediante las enmiendas de gobernanza correspondientes.

---

## Usuarios

- **Usuario de escritorio cotidiano**: Prefiere interactuar mediante ventanas visuales, botones, campos de texto y clics en lugar de comandos de consola; busca una herramienta clara para descargar música individual o álbumes completos con carátula y metadatos sin fricciones técnicas.
- **Coleccionista / Gestor de música sin conexión**: Descarga pistas y listas para escucharlas fuera de línea en sus propios dispositivos y reproductores personales; necesita visibilidad clara de formatos (MP3, M4A, OPUS), estimaciones de descarga y acceso rápido a la carpeta local donde se almacenan los audios.
- **Usuario multitarea**: Pone a descargar una canción o lista y desea continuar buscando o agregando más temas a una cola de espera sin que la interfaz se congele ni le obligue a cambiar de pantalla.

---

## Historias de Usuario

### HU-01: Experiencia gráfica de bienvenida e inicio
- **Como** usuario de la aplicación gráfica,
- **Quiero** acceder a una ventana principal con una barra lateral de navegación organizada y un área central para pegar enlaces o iniciar búsquedas por texto,
- **Para** iniciar mis descargas de manera inmediata sin necesidad de recordar comandos de terminal.

### HU-02: Búsqueda interactiva con lista de opciones
- **Como** usuario que no tiene a mano el enlace directo de un video o canción,
- **Quiero** escribir el título o artista en una pestaña de búsqueda y visualizar los primeros 5 resultados devueltos organizados verticalmente con su información básica (título, canal/artista, versión y duración),
- **Para** seleccionar con un clic el audio exacto que deseo descargar entre las mejores coincidencias.

### HU-03: Configuración visual antes de descargar
- **Como** usuario que ha seleccionado una canción o lista,
- **Quiero** acceder a una vista de opciones claras donde pueda elegir la plataforma de origen (YouTube o YouTube Music), el formato de audio deseado (MP3, M4A u OPUS) y, en caso de listas, definir un límite opcional de canciones,
- **Para** adaptar el archivo a mis preferencias antes de iniciar la transferencia.

### HU-04: Monitoreo en tiempo real y cancelación individual
- **Como** usuario que tiene una descarga activa,
- **Quiero** visualizar en la sección de descargas el avance porcentual, volumen transferido, velocidad, tiempo restante y fase del proceso, con la opción de cancelar la operación si lo requiero,
- **Para** tener certidumbre sobre el estado de la descarga y poder abortarla de forma segura si me equivoqué de pista.

### HU-05: Navegación continua y gestión de cola de descargas
- **Como** usuario que tiene una descarga en curso,
- **Quiero** poder navegar nuevamente a la pantalla de inicio o búsqueda para encolar nuevas canciones recibiendo una confirmación no invasiva, y poder remover canciones de la cola de espera si cambio de opinión,
- **Para** armar mi lista de descargas fluidamente sin interrumpir ni redirigirme forzosamente fuera de mi flujo de búsqueda.

### HU-06: Gestión visual de errores mediante diálogos de acción
- **Como** usuario que ingresa un enlace erróneo o experimenta un fallo de conexión,
- **Quiero** recibir un diálogo modal explicativo y comprensible con opciones directas para reintentar la operación o regresar a la pantalla de inicio,
- **Para** comprender qué ocurrió y recuperarme del error sin que la aplicación se cierre abruptamente.

### HU-07: Consulta y acceso seguro a la biblioteca de descargas
- **Como** usuario que ha descargado varias pistas,
- **Quiero** navegar a la sección de archivos para ver la lista siempre actualizada de canciones guardadas con su formato y duración, y disponer de un botón para abrir directamente la carpeta local en el explorador de archivos del sistema operativo,
- **Para** localizar mis archivos de música sin que la aplicación altere, renombre ni elimine mis ficheros existentes.

---

## Requisitos Funcionales (RF)

### RF-01: Ventana principal y navegación por secciones
- **Descripción**: La interfaz gráfica debe proveer una estructura de ventana con controles personalizados y un menú de navegación lateral para transicionar entre las vistas principales del sistema.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* renderizar una ventana gráfica con controles de ventana (minimizar, maximizar, cerrar), título de la aplicación y navegación lateral.
  - *El sistema debe* proporcionar accesos directos en la barra lateral para tres secciones activas: **Inicio**, **Descargas** y **Archivos**.
  - *Cuando* el usuario seleccione un elemento de la navegación lateral, *el sistema debe* conmutar el panel central a la vista correspondiente sin interrumpir las descargas activas ni perder el estado de la cola.
  - *El sistema debe* mostrar en la navegación lateral la insignia informativa de versión («CODA · v1.0») y la tarjeta informativa indicando que la aplicación es de solo descargas y carece de reproductor integrado.

### RF-02: Captura, pegado y saneamiento de enlaces en pantalla de Inicio
- **Descripción**: La pantalla de inicio debe permitir ingresar direcciones web directas, ofrecer facilidades de pegado desde el portapapeles y sanear enlaces mixtos.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* presentar en la sección **Inicio** un campo de texto para URLs, un botón para pegar el contenido del portapapeles y un botón de acción «Analizar enlace».
  - *Cuando* el usuario pulse el botón de pegar, *el sistema debe* transferir el contenido del portapapeles del sistema operativo al campo de entrada.
  - *Si* el usuario ingresa un enlace mixto correspondiente a un video individual perteneciente a una lista (`watch?v=ID&list=RD...`), *entonces el sistema debe* aplicar poda automática saneando el enlace al video individual para prevenir descargas infinitas accidentales.
  - *Cuando* el usuario active «Analizar enlace» con una URL válida, *el sistema debe* resolver los metadatos iniciales y transicionar a la pantalla de **Opciones de descarga**.
  - *Si* la URL ingresada no es válida o está vacía, *entonces el sistema debe* mostrar un diálogo modal de error indicando la inconsistencia y permitiendo al usuario corregir el enlace.

### RF-03: Búsqueda por nombre y selección en lista vertical
- **Descripción**: La interfaz debe permitir conmutar al modo de búsqueda textual, realizar consultas remotas y desplegar una lista vertical con las 5 mejores coincidencias.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario seleccione la pestaña o botón «Buscar por nombre», *el sistema debe* alternar la entrada a un campo de búsqueda por texto.
  - *Cuando* el usuario ejecute una búsqueda con un término no vacío, *el sistema debe* proyectar un indicador visual de consulta y随后 desplegar la pantalla de **Resultados de búsqueda**.
  - *El sistema debe* presentar los primeros 5 resultados devueltos organizados en una lista vertical, mostrando en cada tarjeta el título, artista o canal, versión, duración y un botón «Elegir audio».
  - *Cuando* el usuario pulse «Elegir audio» en un resultado, *el sistema debe* dirigir a la pantalla de **Opciones de descarga** con la pista seleccionada precargada.
  - *Si* la consulta no arroja coincidencias o ocurre un fallo de red, *entonces el sistema debe* desplegar un diálogo modal informando el estado y ofreciendo reintentar o iniciar una nueva búsqueda.

### RF-04: Configuración de preferencias y encolado no invasivo
- **Descripción**: Vista de parametrización previa a la descarga y adición de tareas a la cola respetando el flujo de trabajo del usuario.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* presentar en la pantalla de **Opciones de descarga** la información básica del audio seleccionado (título, artista/canal y duración).
  - *El sistema debe* permitir elegir la plataforma de origen mediante controles de selección exclusiva (radio buttons para YouTube y YouTube Music).
  - *El sistema debe* permitir elegir el formato de audio de salida mediante selección exclusiva entre **MP3**, **M4A** y **OPUS**.
  - *El sistema debe* establecer que la calidad de audio se procesa en modo automático obteniendo la mejor tasa de bits disponible en la fuente.
  - *Si* el elemento analizado es una lista de reproducción (playlist), *entonces el sistema debe* proveer un campo numérico opcional para limitar la cantidad de canciones a descargar.
  - *Si* el campo de límite de playlist permanece vacío o en cero, *entonces el sistema debe* descargar la lista completa por defecto.
  - *Cuando* el usuario confirme pulsando «Iniciar descarga» y no existan otras descargas en curso, *el sistema debe* iniciar la descarga y dirigir la vista a la sección **Descargas**.
  - *Cuando* el usuario confirme pulsando «Iniciar descarga» existiendo ya una descarga activa en ejecución, *el sistema debe* agregar el elemento al final de la cola de espera, permanecer en la pantalla actual (Inicio o Búsqueda) y emitir un aviso no invasivo (toast/banner) notificando *«Agregado a la cola de descargas»*.
  - *Cuando* el usuario pulse «Cancelar» en la pantalla de opciones, *el sistema debe* descartar la selección y regresar a la vista anterior.

### RF-05: Monitorización de descargas y visualización de progreso
- **Descripción**: La sección de Descargas debe proyectar en tiempo real los eventos de transferencia, conversión y empaquetado de metadatos de la tarea activa.
- **Criterios de Aceptación (EARS)**:
  - *Mientras* una descarga esté en ejecución, *el sistema debe* proyectar la barra de progreso continuo con el porcentaje completado, el volumen transferido (MB descargados vs totales), la velocidad de transferencia y el tiempo estimado restante.
  - *El sistema debe* mostrar secuencialmente la fase activa de la operación:
    1. Preparación y consulta de información.
    2. Transferencia de flujo de audio.
    3. Conversión de formato.
    4. Descarga de carátula e inyección de metadatos ID3.
  - *Si* alguna métrica numérica no está disponible en la fuente para una fase determinada, *entonces el sistema debe* degradar a una animación visual de actividad indeterminada manteniendo la etiqueta textual de la fase.
  - *Cuando* una descarga concluya exitosamente, *el sistema debe* actualizar el estado del elemento a completado y proceder automáticamente con el siguiente elemento encolado.

### RF-06: Gestión de cola de descargas secuencial FIFO y remoción interactiva
- **Descripción**: Orquestación ordenada de tareas pendientes bajo el modelo FIFO con capacidad de descarte anticipado.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* procesar la cola de descargas bajo el principio estricto FIFO (primero en entrar, primero en salir), procesando una única descarga a la vez.
  - *El sistema debe* proyectar en la sección de Descargas tanto la tarea actualmente en ejecución como la lista ordenada de elementos pendientes en espera.
  - *El sistema debe* permitir al usuario remover o descartar cualquier elemento pendiente de la cola de espera antes de que comience su ejecución mediante un botón individual de eliminación.
  - *Cuando* una descarga en curso termine (por éxito, fallo no recuperable o cancelación individual), *el sistema debe* iniciar inmediatamente la descarga del siguiente elemento disponible en la cola.

### RF-07: Cancelación interactiva y saneamiento de temporales
- **Descripción**: Control de aborto de la descarga activa garantizando la eliminación de archivos residuales y la continuidad de la cola.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario pulse el botón «Cancelar descarga» sobre la tarea activa, *el sistema debe* detener de inmediato el proceso de obtención y conversión de audio.
  - *Cuando* se cancele la descarga activa, *el sistema debe* suprimir cualquier archivo temporal o incompleto generado en el disco para dicha pista.
  - *Si* la tarea activa es cancelada y existen elementos pendientes en la cola, *entonces el sistema debe* permanecer en la sección **Descargas**, notificar la cancelación puntual e iniciar la siguiente descarga encolada.
  - *Si* la tarea activa es cancelada y no existen más elementos en la cola, *entonces el sistema debe* retornar al usuario a la pantalla de **Inicio** con un aviso confirmando la cancelación de la descarga.

### RF-08: Gestión de fallos y resiliencia visual mediante modales
- **Descripción**: Tratamiento de excepciones mediante ventanas modales interactivas con alternativas claras de recuperación.
- **Criterios de Aceptación (EARS)**:
  - *Si* ocurre un fallo crítico de red, restricción de contenido privado o ausencia del binario FFmpeg, *entonces el sistema debe* desplegar un diálogo modal en primer plano con el diagnóstico comprensible en español.
  - *El sistema debe* proveer en dicho diálogo modal dos opciones de acción: «Reintentar» (para intentar reanudar la operación sobre la pista actual) y «Aceptar / Volver al inicio» (para limpiar temporales, descartar la pista y retornar de forma segura).
  - *Si* una pista individual de una lista de reproducción falla durante la transferencia o codificación, *entonces el sistema debe* registrar el error en la bitácora, mostrar una alerta visual no bloqueante y continuar con las canciones restantes de la lista.

### RF-09: Catálogo de archivos descargados con auto-refresco y apertura segura
- **Descripción**: Vista de biblioteca para consultar el almacenamiento local, respetando la intangibilidad de los archivos del usuario.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario interactúe o ingrese a la sección **Archivos**, *el sistema debe* escanear automáticamente el directorio local de descargas (`downloads/`) para reflejar en tiempo real altas, bajas o modificaciones manuales externas.
  - *El sistema debe* listar los archivos de audio soportados (`.mp3`, `.m4a`, `.opus`) mostrando nombre del fichero, formato detectado y estado de guardado.
  - *El sistema debe* incluir en la cabecera un botón para «Abrir carpeta», el cual abrirá la ruta física de descargas en el explorador de archivos nativo del sistema operativo.
  - *El sistema debe* prohibir de forma estricta cualquier mecanismo o botón para editar, renombrar o eliminar archivos desde la vista de la aplicación, garantizando que la interfaz actúe únicamente como panel de consulta.
  - *Si* el directorio no contiene archivos de audio, *entonces el sistema debe* desplegar un estado vacío informativo con un botón de acción principal «Nueva descarga» que conduzca a Inicio.

---

## Requisitos No Funcionales (RNF)

- **RNF-01 (Conformidad constitucional de dependencias)**: La interfaz gráfica se desarrollará sobre la librería Python Flet. Su adopción formal se ratifica mediante una enmienda explícita a la Regla 1 de la Constitución del proyecto y su correspondiente justificación técnica en `MEMORY.md`.
- **RNF-02 (Separación e independencia arquitectónica MVC)**: La vista gráfica implementará el contrato formal `ViewInterface`. Los componentes de dominio (`core/`) y procesamiento de metadatos (`metadata/`) permanecerán completamente agnósticos de Flet y de la capa de interfaz (Regla 3 de la Constitución).
- **RNF-03 (Archivos del usuario sagrados)**: La aplicación únicamente leerá y escribirá archivos de audio dentro del directorio local `downloads/`, y registros en `app.log`. La interfaz no poseerá capacidades de modificación ni borrado de archivos del usuario (Regla 5 de la Constitución).
- **RNF-04 (Idioma)**: El 100% de los elementos visibles, botones, etiquetas, avisos no invasivos, diálogos modales y mensajes de error proyectados en la interfaz gráfica deben expresarse rigurosamente en idioma español (Regla 6 de la Constitución).
- **RNF-05 (Fidelidad visual al diseño Figma «CODA»)**: La disposición de elementos, proporciones, paleta de colores, tipografía, jerarquía visual y estados interactivos deben corresponder con exactitud al prototipo interactivo de Figma.
- **RNF-06 (Fluidez y responsividad sin bloqueos)**: Las operaciones pesadas de red, extracción de flujos de audio y codificación FFmpeg deben ejecutarse de forma asíncrona o en hilos de trabajo desacoplados del hilo principal de la interfaz, garantizando una tasa de refresco fluida de 60 FPS sin congelamientos.
- **RNF-07 (Ejecución de pruebas en modo headless)**: Las pruebas automatizadas de la capa de vista y de los adaptadores deben ejecutarse en memoria (*mocks/fakes*) sin requerir renderizado gráfico físico ni dependencias de pruebas externas, asegurando que `pytest tests/ -v` se ejecute al 100% en entornos CI/headless (Regla 4 de la Constitución).

---

## Casos Límite

1. **Colisión de nombres de archivo idénticos en descargas consecutivas**: Si se intenta descargar una canción cuyo nombre de archivo y formato ya existen físicamente dentro de `downloads/`, el sistema aplica automáticamente un sufijo numérico incremental (por ejemplo `Cancion (1).mp3`) para preservar la descarga existente sin sobreescribirla ni abortar la tarea.
2. **Remoción de una canción encolada mientras otra se descarga**: El usuario pulsa el botón de remover sobre la tercera canción de la cola; el sistema la extrae de la lista en memoria inmediatamente sin afectar el progreso ni los temporales de la descarga activa.
3. **Cancelación de la tarea activa con cola remanente**: Si se cancela la canción activa y aún restan 2 canciones en la cola, el sistema purga los archivos temporales de la pista cancelada, permanece en la sección Descargas y arranca de inmediato la siguiente descarga encolada.
4. **Manipulación externa del directorio de descargas**: Si el usuario borra o renombra archivos en `downloads/` a través del explorador del sistema, al volver o interactuar con la pestaña Archivos la vista se actualiza automáticamente leyendo el nuevo estado del disco sin desincronizaciones.
5. **Entrada de URLs con parámetros de mezcla infinita (`&list=RD...`)**: El analizador detecta la discrepancia y aplica la poda automática de mix, extrayendo el video individual y alertando pedagógicamente al usuario de la adaptación.
6. **Cancelación en fase de inyección de metadatos o fallo de carátula**: Si la transferencia del audio concluyó pero la inyección de la imagen o tags falla por error técnico, el archivo de audio se conserva intacto en el disco, se notifica la advertencia y no se elimina el fichero.
7. **Pistas sin imagen o con formatos de carátula WebP/no estándar**: La interfaz gráfica degrada elegantemente desplegando un icono neutro de audio en la tarjeta de resultado y en la biblioteca sin interrumpir el flujo.
8. **Intento de descarga con espacio insuficiente en disco o sin binario FFmpeg**: El sistema intercepta la condición antes de corromper la cola, emite un diálogo modal con instrucciones de solución y mantiene las tareas pendientes pausadas o a salvo.
9. **Cierre de la ventana principal con descargas activas en la cola**: Al presionar el control de cerrar de la ventana con tareas en progreso, el sistema despliega un diálogo de confirmación («Hay descargas en curso. ¿Deseas detenerlas y salir?») para evitar pérdidas accidentales de progreso.

---

## Fuera de Alcance

- **Reproductor de audio integrado**: La aplicación no incorporará controles de reproducción multimedia (play, pause, seekbar, volumen); la escucha de audios se delega al reproductor predeterminado del sistema operativo.
- **Sección de Ajustes**: La sección de Ajustes se excluye formalmente de esta versión; las configuraciones de formato predeterminado y directorios se rigen por la configuración base del sistema.
- **Descargas concurrentes / paralelas (multidescarga)**: No se ejecutarán múltiples descargas simultáneas en paralelo en esta fase; el procesamiento de la cola de descargas será estrictamente secuencial FIFO (una tarea activa a la vez).
- **Modificación o borrado de archivos desde la GUI**: La interfaz gráfica no ofrecerá botones ni opciones para eliminar, renombrar o reetiquetar archivos existentes en el almacenamiento local.
- **Edición manual de metadatos ID3**: No se incluirá un editor interactivo para personalizar campos de artista o álbum.
- **Sincronización en la nube o cuentas de streaming**: Coda no implementará inicio de sesión ni sincronización con cuentas de Google o YouTube.

---

## Criterios de Finalización (Definition of Done)

1. **Enmienda formal de la Constitución**: Se ha actualizado `docs/constitution.md` (Regla 1) para autorizar formalmente la incorporación de `flet` como dependencia de producción para la capa gráfica, con su justificación técnica registrada en `MEMORY.md`.
2. **Sincronización de AGENTS.md**: Se ha actualizado `AGENTS.md` (Regla 2 de la Constitución) reflejando la nueva vista gráfica, la interacción con la cola secuencial y los comandos de ejecución.
3. **Fidelidad al prototipo Figma**: Las pantallas de Inicio, Búsqueda, Resultados (5 elementos en lista vertical), Opciones, Descarga activa, Éxito y Archivos descargados reflejan fielmente el diseño «CODA».
4. **Cumplimiento del contrato abstracto**: La vista gráfica implementa `ViewInterface` y reacciona a eventos neutros de progreso sin acoplar dependencias visuales en `core/` ni `metadata/`.
5. **Cola secuencial FIFO interactiva**: Se verifica la capacidad de encolar múltiples descargas con avisos no invasivos, remover canciones pendientes de la cola y procesar automáticamente una tras otra.
6. **Resolución de colisiones y sufijos numéricos**: Se comprueba que canciones con nombres duplicados reciben sufijos secuenciales (`Cancion (1).mp3`) sin sobrescribir ni corromper archivos previos.
7. **Resiliencia modal y cancelación limpia**: Se comprueba que los errores despliegan diálogos modales interactivos y que la cancelación individual purga temporales e inicia la siguiente tarea encolada.
8. **Auto-refresco de biblioteca**: La pestaña Archivos actualiza su contenido al interactuar con ella reflejando altas o bajas externas en `downloads/`.
9. **Integridad de pruebas headless**: El 100% de la suite de pruebas pasa satisfactoriamente con `pytest tests/ -v`, ejecutando pruebas sobre los adaptadores de la vista mediante simulaciones en memoria sin necesidad de interfaz gráfica activa.

---

## Dudas Abiertas

- `[NECESITA ACLARACIÓN]` **Persistencia de la cola de descargas entre sesiones**: Si la aplicación se cierra con elementos pendientes en la cola, ¿deben persistir en disco para reanudarse en la siguiente apertura o la cola es puramente efímera en memoria para la sesión activa?
- `[NECESITA ACLARACIÓN]` **Filtro de búsqueda en la biblioteca de Archivos**: Cuando el usuario acumula decenas o cientos de canciones en `downloads/`, ¿se contemplará un buscador de texto local dentro de la pestaña Archivos para filtrar la tabla rápidamente o se mantendrá el listado cronológico simple?
