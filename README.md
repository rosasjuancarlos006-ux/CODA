# Coda — YouTube & YouTube Music Downloader

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Platforms-YouTube%20%7C%20YouTube%20Music-red?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/Formats-MP3%20%7C%20M4A%20%7C%20OPUS-orange?style=for-the-badge" alt="Audio Formats" />
  <img src="https://img.shields.io/badge/Interface-Rich%20CLI-magenta?style=for-the-badge" alt="Rich CLI" />
</p>

**Coda** es una herramienta de terminal profesional en Python para buscar y descargar música o playlists completas desde **YouTube** y **YouTube Music** en formato **MP3**, **M4A** u **OPUS**, con selección interactiva por operación, carátulas originales, metadatos ID3 automáticos y una interfaz moderna basada en Rich.

---

## ✨ Características

- 🌐 **Soporte Multiplataforma Inteligente**:
  - Descarga desde **YouTube general** (videos, conciertos, directos) o **YouTube Music** (pistas de estudio oficiales, álbumes).
  - Selector interactivo con opciones `[1] YouTube` y `[2] YouTube Music` (Enter = YouTube).
  - **Auto-adaptación y tolerancia de enlaces**: Si seleccionas YouTube pero ingresas un enlace de YouTube Music (o viceversa), Coda detecta el enlace, muestra un aviso amigable en español y descarga el contenido automáticamente sin abortar la operación.
  - **Inferencia automática en CLI**: Al pasar un enlace directo por terminal (`python main.py <url>`), Coda detecta la plataforma automáticamente sin hacer preguntas redundantes.
  - **Saneamiento automático de mixes**: Descarga pistas individuales limpias incluso si el enlace contiene listas infinitas (`&list=RD...`).
- 🎵 **Soporte multiformato dinámico**: Elige entre `mp3`, `m4a` u `opus` en cada descarga (canciones individuales y playlists) con opción predeterminada rápida (`Enter = mp3`).
- 🛡️ **Prompt guiado con reintentos**: Validación automática de formato y plataforma, tolerancia a mayúsculas/espacios y hasta 3 reintentos antes de seleccionar valores por defecto.
- 🔍 **Búsqueda inteligente**: Búsqueda por texto orientada según la plataforma elegida (en YouTube Music prioriza versiones oficiales de audio).
- 🔗 **Descarga directa**: Soporte para enlaces directos de videos individuales de YouTube y YouTube Music.
- 📑 **Descarga de Playlists completas**: Descarga listas enteras con formato unificado, límite configurable de pistas y barra de progreso.
- 🏷️ **Metadatos y carátulas con degradación elegante**: Inyección automática de etiquetas ID3v2 (Título, Artista, Álbum) y carátula frontal APIC para MP3; preserva el archivo de audio intacto ante limitaciones técnicas en otros contenedores.
- 💻 **UX moderna en consola con Rich**: Paneles interactivos, banners ASCII, tablas detalladas para la biblioteca local y barras de progreso fluidas.
- 📝 **Registro y trazabilidad**: Bitácora técnica completa de operaciones y errores en `app.log`.
- 🛡️ **Manejo de excepciones robusto**: Mensajes claros ante fallos comunes (videos privados, sin conexión, restricciones de edad).

---

## 📸 Vista Previa

```text
   ______ ____  ____   ___ 
  / ____// __ \/ __ \ /   |
 / /    / / / / / / // /| |
/ /___ / /_/ / /_/ // ___ |
\____/ \____/_____//_/  |_|

YouTube Music Downloader • High Quality Audio & ID3 Tags

┌───────────────────────────── Panel de Control ──────────────────────────────┐
│                                                                             │
│    [1] Descargar música (Canción individual, Búsqueda o Playlist)           │
│    [2] Ver biblioteca de descargas local                                    │
│    [3] Salir de Coda                                                        │
│                                                                             │
└───────────────────── Selecciona una opción del 1 al 3 ──────────────────────┘
```

### Selector de plataforma y descarga interactiva:
```text
Plataforma de Descarga
  [1] YouTube (Catálogo general, videos, directos)
  [2] YouTube Music (Pistas oficiales, álbumes, música de estudio)

Selecciona una plataforma [1/2] (Enter = YouTube): 2

Descargar desde YouTube Music
Ingresa la URL (video/playlist) o término de búsqueda: Coldplay Yellow
ℹ Búsqueda en YouTube Music: 'Coldplay Yellow'. Buscando el mejor resultado...
Formato de audio [mp3/m4a/opus] (Enter = mp3): mp3
```

---

## ⚙️ Requisitos Previos

1. **Python 3.10 o superior**.
2. **FFmpeg**: Necesario para la extracción y conversión a MP3, M4A y OPUS.

### 📥 Cómo obtener FFmpeg

Coda busca FFmpeg automáticamente en dos lugares:
1. En el **PATH** del sistema.
2. O en una carpeta local llamada `bin/` dentro de la raíz del proyecto (`bin/ffmpeg.exe` y `bin/ffprobe.exe`).

#### Opción A (Recomendada en Windows con Scoop o Winget):
```powershell
winget install Gyan.FFmpeg
# o con Scoop:
scoop install ffmpeg
```

#### Opción B (Binarios locales en la carpeta `bin/`):
1. Descarga el paquete comprimido de [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) (Release builds essentials).
2. Extrae `ffmpeg.exe` y `ffprobe.exe`.
3. Crea la carpeta `bin/` en la raíz de Coda y pega ambos archivos allí:
   ```text
   coda/
   ├── bin/
   │   ├── ffmpeg.exe
   │   └── ffprobe.exe
   ```

---

## 🚀 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/rosasjuancarlos006-ux/Coda.git
   cd Coda
   ```

2. **Crear y activar un entorno virtual (opcional pero recomendado)**:
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux/macOS:
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎵 Uso

### 1. Modo Interactivo (Recomendado)
Inicia la interfaz completa de Coda:
```bash
python main.py
```
Te permitirá navegar por el menú, elegir la plataforma (`YouTube` o `YouTube Music`), buscar canciones, ingresar playlists, elegir el formato de salida deseado (`mp3`, `m4a`, `opus`) o explorar tu biblioteca de descargas local.

### 2. Modo Directo por Argumentos (CLI)
Si prefieres pasar la canción o playlist directamente desde la terminal, Coda detectará automáticamente si el enlace proviene de YouTube o YouTube Music:

- **Por nombre de canción**:
  ```bash
  python main.py "The Beatles - Yesterday"
  ```
- **Por URL de video de YouTube Music**:
  ```bash
  python main.py "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
  ```
- **Por URL de video de YouTube general**:
  ```bash
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ```
- **Descargar Playlist (con límite de pistas)**:
  ```bash
  python main.py "https://music.youtube.com/playlist?list=PL..." -l 10
  ```
- **Carpeta de salida personalizada**:
  ```bash
  python main.py "Queen Bohemian Rhapsody" -o "./mi_musica"
  ```

---

## 🧪 Pruebas Unitarias

Para ejecutar la suite completa de pruebas automatizadas con `pytest`:
```bash
pytest tests/ -v
```

---

## 📁 Estructura del Proyecto

```text
coda/
├── core/
│   ├── downloader.py          # Orquestación con yt-dlp y conversión multiformato
│   └── resolver.py            # Resolución y contextualización según plataforma
├── metadata/
│   └── writer.py              # Tags ID3v2, portadas y degradación elegante
├── ui/
│   ├── cli.py                 # Parseo de argumentos con argparse
│   └── display.py             # Interfaz visual con Rich (plataforma, formato, tablas)
├── utils/
│   ├── file_manager.py        # Sanitización de nombres de archivo
│   ├── format_validator.py    # Validación y normalización pura de formatos
│   ├── platform_validator.py  # Validación pura de plataformas y chequeo de enlaces
│   └── validator.py           # Detección de URLs y saneamiento de mixes
├── tests/
│   ├── test_file_manager.py
│   ├── test_format_validator.py
│   ├── test_platform_validator.py
│   ├── test_validator.py
│   ├── test_resolver.py
│   ├── test_display_platform.py
│   └── test_main_orchestration.py
├── downloads/                 # Directorio donde se guardan los archivos de audio
├── config.py                  # Configuraciones globales y logging
├── main.py                    # Punto de entrada y orquestación del flujo
├── requirements.txt           # Dependencias de producción
├── LICENSE                    # Licencia MIT
└── README.md
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

Desarrollado con ❤️ por [@rosasjuancarlos006-ux](https://github.com/rosasjuancarlos006-ux).
