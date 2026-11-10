# Especificación de Requisitos — Modularización y Desacoplamiento de Interfaz (Modelo-Vista-Controlador)

## Contexto y Objetivo

Actualmente, el sistema coordina sus flujos de usuario, la captura de entradas interactivas y la emisión de elementos visuales de manera fuertemente acoplada en su punto de entrada principal. Aunque la lógica de extracción de audio y el procesamiento de metadatos residen en componentes separados, la presentación y el control de flujo están entremezclados. Esto dificulta la sustitución de la interfaz actual de terminal por interfaces modernas (tales como interfaces gráficas de escritorio) sin tener que reescribir la lógica de coordinación.

El objetivo de esta funcionalidad es desacoplar completamente la capa de presentación de la capa de coordinación y de las reglas de negocio, adoptando conceptualmente el patrón Modelo-Vista-Controlador. Esto permitirá que la interfaz sea un componente intercambiable mediante contratos abstractos bien definidos, asegurando cero regresión en las capacidades actuales de terminal y proporcionando un flujo interactivo mucho más resiliente frente a errores de entrada, fallos de red, ausencias de dependencias y cancelaciones del usuario.

---

## Usuarios

- **Usuario interactivo en terminal**: Desea una experiencia guiada por menús, clara y tolerante a fallos, que le permita corregir datos erróneos de inmediato o reintentar descargas fallidas sin perder la sesión de la aplicación, así como cancelar descargas en curso y regresar ordenadamente al menú principal.
- **Usuario de línea de comandos (Automatización / Scripts)**: Invoca el sistema suministrando parámetros directos para descargas puntuales; requiere terminación rápida, códigos de salida estándar ante fallos, limpieza automática de archivos incompletos y ausencia total de bloqueos interactivos.
- **Diseñador / Desarrollador de interfaces**: Requiere un contrato abstracto y limpio para conectar nuevas vistas (por ejemplo, una futura interfaz gráfica) interactuando con el sistema mediante eventos de datos neutros, sin alterar la lógica de coordinación ni el motor de descarga.

---

## Historias de Usuario

### HU-01: Experiencia interactiva sin regresiones
- **Como** usuario habitual del sistema en modo interactivo,
- **Quiero** realizar mis búsquedas y descargas con la misma fluidez, orden y retroalimentación estética visual que poseo actualmente,
- **Para** mantener mi flujo de trabajo habitual sin percibir cambios negativos ni pérdidas de funciones.

### HU-02: Recuperación interactiva ante fallos recuperables
- **Como** usuario en modo interactivo,
- **Quiero** que si cometo un error de tipeo en un dato o si ocurre un fallo puntual de conexión, el sistema me informe la situación de forma clara y me permita corregir el dato en el momento o regresar al menú principal,
- **Para** no perder el contexto de mi sesión ni tener que reiniciar el programa desde cero.

### HU-03: Cancelación limpia y retorno al menú
- **Como** usuario que inicia una descarga interactiva por error o decide detenerla a la mitad,
- **Quiero** poder cancelar la operación en curso de forma segura para que se limpien los archivos incompletos y el sistema me regrese al menú principal,
- **Para** continuar usando la herramienta sin que la aplicación se cierre abruptamente.

### HU-04: Ejecución directa predecible para automatizaciones
- **Como** usuario que ejecuta la herramienta mediante comandos directos con parámetros,
- **Quiero** que el procesamiento se efectúe sin preguntas interactivas y que cualquier error cause la finalización inmediata con un código de salida apropiado,
- **Para** poder integrar la herramienta de manera confiable en scripts de automatización.

### HU-05: Visibilidad en tiempo real del avance por fases
- **Como** usuario que descarga canciones individuales o listas de reproducción,
- **Quiero** recibir información en tiempo real sobre el estado específico de cada fase (preparación, transferencia del flujo de audio con métricas, conversión de formato e inyección de metadatos) y el avance elemento a elemento en listas,
- **Para** conocer con precisión el estado del proceso y saber cuánto tiempo tomará finalizarlo.

---

## Requisitos Funcionales (RF)

### RF-01: Aislamiento total mediante contrato abstracto de presentación
- **Descripción**: La captura de datos de entrada y la presentación de información visual deben residir en un componente de vista independiente, desacoplado de la coordinación y del dominio.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* prohibir que los componentes de dominio y coordinación invoquen directamente mecanismos específicos de renderizado o captura de consola.
  - *Cuando* la coordinación requiera solicitar información al usuario o notificar un resultado, *el sistema debe* comunicarse exclusivamente a través de un contrato formal de presentación (métodos abstractos para solicitud de opciones, captura de texto, despliegue de mensajes, tablas y actualización de progreso).
  - *El sistema debe* permitir que la implementación de la vista sea reemplazada por otra presentación compatible sin alterar las reglas de negocio ni el flujo de coordinación.

### RF-02: Ciclo interactivo y taxonomía de errores
- **Descripción**: El modo interactivo debe clasificar los fallos y ofrecer una recuperación contextual que evite el cierre prematuro de la aplicación.
- **Criterios de Aceptación (EARS)**:
  - *Si* ocurre un error de validación de entrada (dirección web inválida, opción inexistente, límite no numérico), *entonces el sistema debe* reportar el mensaje explicativo a la vista y volver a solicitar el campo específico inmediatamente, permitiendo al usuario ingresar una opción de escape o cancelación para volver al menú.
  - *Si* ocurre un fallo operativo recuperable durante la descarga (corte temporal de red, recurso no disponible o video privado), *entonces el sistema debe* emitir la notificación de error a la vista y retornar al menú principal de manera limpia sin abortar el proceso.
  - *Si* ocurre un fallo crítico de entorno (ausencia del binario de conversión de audio o imposibilidad de escribir en el disco), *entonces el sistema debe* mostrar una advertencia detallada con las instrucciones para solucionarlo y retornar al menú principal en modo interactivo.

### RF-03: Control de cancelaciones y política de eliminación de archivos
- **Descripción**: Gestión de interrupciones del usuario y diferenciación entre cancelación y degradación técnica.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario solicite la cancelación de una descarga interactiva mediante una señal de interrupción, *el sistema debe* detener inmediatamente el proceso en el límite del fragmento en curso.
  - *Cuando* una operación sea cancelada por el usuario (o si el flujo de audio quedó truncado por corte irrecuperable), *el sistema debe* eliminar los archivos parciales o temporales generados y retornar al menú principal.
  - *Si* una descarga de audio concluyó exitosamente pero la inyección posterior de carátula o metadatos falla por error técnico en tiempo de ejecución, *entonces el sistema debe* conservar el archivo de audio intacto, emitir una advertencia visible y registrar el incidente sin eliminar la canción descargada.

### RF-04: Ejecución directa no interactiva por línea de comandos
- **Descripción**: Garantía de comportamiento determinista para ejecuciones directas con parámetros.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el sistema se inicie con parámetros directos de búsqueda o descarga, *el sistema debe* procesar la solicitud omitiendo los menús y diálogos interactivos de bienvenida.
  - *Si* la operación directa finaliza satisfactoriamente, *entonces el sistema debe* emitir el resumen de éxito a la vista y terminar con código de salida exitoso (0).
  - *Si* ocurre un fallo o interrupción durante una ejecución directa, *entonces el sistema debe* emitir el mensaje de error a la vista, suprimir los residuos temporales incompletos generados y finalizar inmediatamente con un código de error (distinto de 0), sin solicitar reintentos manuales.

### RF-05: Emisión de eventos de progreso agnósticos y degradación visual
- **Descripción**: Notificaciones del avance de operaciones desacopladas de la tecnología visual.
- **Criterios de Aceptación (EARS)**:
  - *El sistema debe* emitir eventos de progreso desde el dominio y la coordinación hacia la vista utilizando estructuras de datos neutras (fase actual, porcentaje numérico, velocidad, tiempo estimado, elemento actual y total de elementos).
  - *Mientras* se procesa una operación, *el sistema debe* notificar el cambio secuencial entre fases:
    1. Preparación y consulta de información.
    2. Transferencia de audio.
    3. Conversión de formato.
    4. Descarga de imagen e inyección de metadatos.
  - *Si* métricas específicas como porcentaje, velocidad o tiempo estimado no están disponibles en una fase, *entonces el sistema debe* degradar en la vista mostrando un indicador de actividad continua (animación indeterminada) junto con la descripción textual de la fase en español.
  - *Mientras* se procesa una lista de reproducción, *el sistema debe* notificar a la vista el número de elemento en curso y el total de la colección.
  - *Si* una pista individual de una lista de reproducción falla durante la transferencia o conversión, *entonces el sistema debe* emitir la alerta correspondiente a la vista, registrar el fallo y continuar con las canciones restantes de la colección.

### RF-06: Consulta y reporte del directorio de descargas
- **Descripción**: Provisión desacoplada para la visualización del contenido descargado localmente.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario solicite consultar las descargas disponibles en el modo interactivo, *el sistema debe* escanear el directorio de destino filtrando exclusivamente archivos con extensiones de audio soportadas (`.mp3`, `.m4a`, `.opus`).
  - *Si* el directorio no contiene archivos de audio soportados, *entonces el sistema debe* solicitar a la vista que muestre un mensaje informativo en español indicando que no hay canciones descargadas aún, sin emitir errores ni tablas vacías.
  - *Cuando* existan canciones válidas, *el sistema debe* transferir la lista estructurada a la vista para su representación tabular organizada (nombre de archivo, formato, tamaño y fecha de modificación).

### RF-07: Respeto del orden de interacción y listas vacías
- **Descripción**: Preservar la secuencia del flujo interactivo y manejar listas sin elementos viables.
- **Criterios de Aceptación (EARS)**:
  - *Cuando* el usuario inicie una descarga desde el menú interactivo, *el sistema debe* requerir la información en el siguiente orden estricto:
    1. Selección de plataforma de origen (con valor predeterminado y tolerancia a alias).
    2. Entrada de enlace o consulta (con detección pedagógica de discrepancia de plataforma y auto-adaptación sin abortar).
    3. Límite de canciones (únicamente si se detectó una lista de reproducción).
    4. Formato de audio deseado.
    5. Procesamiento y presentación del resumen final.
  - *Si* una lista de reproducción consultada no contiene pistas viables (lista vacía o todas las pistas privadas/bloqueadas), *entonces el sistema debe* emitir un aviso informativo en español indicando que no hay contenido descargable y regresar limpiamente al menú principal, sin crear archivos vacíos ni generar fallos no controlados.

---

## Requisitos No Funcionales (RNF)

- **RNF-01 (Stack mínimo)**: El desacoplamiento y los contratos deben lograrse exclusivamente con las capacidades nativas del lenguaje y las dependencias previamente aprobadas en el proyecto, sin incorporar librerías externas adicionales.
- **RNF-02 (Separación e independencia estricta)**: La capa de dominio nunca debe importar ni referenciar clases, funciones o tipos de la capa de presentación. La vista únicamente reacciona a eventos y llamadas procedentes de la coordinación.
- **RNF-03 (Protección de archivos del usuario)**: El sistema únicamente puede crear archivos dentro del directorio de descargas y registrar eventos en la bitácora del sistema. Todo residuo temporal generado por cancelaciones del usuario debe ser suprimido automáticamente.
- **RNF-04 (Idioma)**: Todos los textos, opciones de menú, mensajes informativos, advertencias y reportes mostrados al usuario final deben expresarse exclusivamente en idioma español.
- **RNF-05 (Rendimiento y responsividad)**: Las notificaciones periódicas de progreso no deben introducir retardos perceptibles ni bloquear la recepción inmediata de señales de cancelación del usuario.

---

## Casos Límite

1. **Cancelación del usuario en fases intermedias**: Si el usuario interrumpe la ejecución mediante Ctrl+C mientras se ejecuta la conversión de formato o la inyección de metadatos, el sistema suprime los archivos incompletos generados en dicha operación y retorna al menú interactivo.
2. **Degradación técnica de metadatos**: Si la pista se descargó al 100% pero la carátula o los campos de metadatos fallan por error técnico, el archivo de audio se conserva intacto en el disco y se muestra una advertencia.
3. **Falla parcial en elementos de una lista de reproducción**: Si una o más canciones de una lista fallan por restricciones de acceso o derechos de autor, el proceso continúa con las pistas restantes y emite un balance final diferenciando éxitos y fallos.
4. **Entradas vacías o de puros espacios**: El sistema detecta la ausencia de contenido, emite una advertencia comprensible y solicita nuevamente el dato sin corromper el flujo.
5. **Entorno sin binarios de conversión o sin permisos de escritura**: El sistema intercepta el problema antes de iniciar descargas corruptas, emite el diagnóstico en español y retorna al menú principal.
6. **Múltiples cancelaciones rápidas consecutivas**: Si el usuario envía múltiples señales de interrupción seguidas mientras se ejecuta la limpieza de archivos, el sistema las absorbe de forma controlada garantizando que el proceso de limpieza concluya sin desbordamientos de pila ni salidas abruptas con rastros de error.
7. **Directorio de salida inexistente**: Si la carpeta de descargas no existe o fue eliminada durante la sesión, el sistema debe recrearla de manera automática y transparente antes de intentar almacenar nuevos archivos.

---

## Fuera de Alcance

- **Implementación de una interfaz gráfica (GUI)**: La codificación de una interfaz gráfica de usuario (de escritorio, web o móvil) no forma parte de esta entrega. Esta fase se limita estrictamente a la refactorización arquitectónica desacoplada manteniendo la vista de terminal existente.
- **Servicios web o APIs remotas**: No se implementarán servidores HTTP, endpoints REST ni sockets de red.
- **Cambios en los motores de conversión o formatos de audio**: No se agregarán nuevos formatos de codificación de audio ni se sustituirán los motores de descarga y etiquetado existentes.
- **Descargas simultáneas o concurrentes**: Se mantiene el modelo secuencial y ordenado para el procesamiento de pistas y listas de reproducción.

---

## Criterios de Finalización (Definition of Done)

1. **Enmienda constitucional y de gobierno**: Se ha actualizado formalmente `docs/constitution.md` (Regla 4) para autorizar pruebas unitarias del controlador y de los contratos de presentación utilizando vistas simuladas (*mocks*/*fakes* en memoria) sin agregar dependencias externas de prueba.
2. **Sincronización de AGENTS.md**: Se ha actualizado `AGENTS.md` (Regla 2 de la Constitución) reflejando la nueva arquitectura MVC, la redistribución de responsabilidades y la estructura de módulos antes de dar por terminada la fase.
3. **Contrato de presentación formalizado**: Existe una interfaz o protocolo abstracto que define los métodos de interacción que cualquier vista debe implementar.
4. **Cero regresiones en la experiencia de terminal**: Todas las funcionalidades de descarga individual, listas de reproducción, selección de plataformas, auto-adaptación de enlaces y resumen tabular siguen operando idénticamente en la consola.
5. **Resiliencia interactiva comprobada**: Los errores de entrada permiten reintentar el campo específico; los fallos operativos y de entorno retornan limpiamente al menú principal; la cancelación con Ctrl+C regresa al menú sin abortar la aplicación y limpiando archivos temporales.
6. **Comportamiento CLI directo preservado**: Las ejecuciones con parámetros directos terminan con códigos de salida estándar (0 en éxito, no cero en fallo) y limpian archivos temporales si son interrumpidas.
7. **Eventos granulares funcionando**: La vista recibe estructuras de datos neutras y proyecta el progreso en tiempo real de cada fase, con degradación visual a animaciones continuas cuando no hay métricas numéricas.
8. **Integridad de pruebas**: El 100% de la suite de pruebas automatizadas pasa satisfactoriamente con `pytest tests/ -v`, incluyendo las nuevas pruebas sobre el controlador y los contratos.

---

## Dudas Abiertas

- `[NECESITA ACLARACIÓN]` **Persistencia de preferencias del usuario entre sesiones**: Cuando se adopte una interfaz gráfica a futuro, ¿debería el sistema recordar configuraciones preferidas (como el formato de audio favorito o la carpeta de descarga habitual), o se mantendrán siempre los valores predeterminados fijados en la configuración global? Para la presente fase se mantendrán los valores por defecto sin persistencia de estado local.
- `[NECESITA ACLARACIÓN]` **Notificaciones de finalización a nivel de sistema operativo**: ¿Debería la capa de presentación emitir notificaciones sonoras o de escritorio cuando una descarga extensa en segundo plano finaliza, o se limita a la retroalimentación visual interna de la vista?
