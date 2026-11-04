# Coda — YouTube Music Downloader

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Audio-MP3%20192%20kbps-orange?style=for-the-badge" alt="Audio MP3" />
  <img src="https://img.shields.io/badge/Interface-Rich%20CLI-magenta?style=for-the-badge" alt="Rich CLI" />
</p>

**Coda** es una herramienta de terminal profesional en Python para buscar y descargar música o playlists completas desde YouTube en formato MP3 de alta calidad (192 kbps), incorporando automáticamente carátulas originales y metadatos ID3v2.

---

## ✨ Características

- 🔍 **Búsqueda inteligente**: Descarga canciones ingresando su título sin necesidad de abrir el navegador.
- 🔗 **Descarga directa**: Soporte para enlaces directos de videos individuales de YouTube.
- 📑 **Descarga de Playlists completas**: Descarga listas enteras con límite configurable de pistas y barra de progreso.
- 🏷️ **Metadatos ID3 automáticos**: Inyección de etiquetas ID3v2 (Título, Artista parseado, Álbum).
- 🖼️ **Carátula frontal integrada (APIC)**: Incrusta la portada en alta resolución directamente en el archivo `.mp3`.
- 💻 **UX moderna en consola con Rich**: Paneles interactivos, banners ASCII, tablas para la biblioteca local y barras de progreso fluidas.
- 📝 **Registro y trazabilidad**: Bitácora de operaciones y errores en `app.log`.
- 🛡️ **Manejo de excepciones robusto**: Mensajes claros ante fallos comunes (videos privados, sin conexión, restricciones de edad).

---

## 📸 Vista Previa

```text
   ______ ____  ____   ___ 
  / ____// __ \/ __ \ /   |
 / /    / / / / / / // /| |
/ /___ / /_/ / /_/ // ___ |
\____/ \____/_____//_/  |_|

YouTube Music Downloader • High Quality MP3 & ID3 Tags

┌───────────────────────────── Panel de Control ──────────────────────────────┐
│                                                                             │
│    [1] Descargar música (Canción individual, Búsqueda o Playlist)           │
│    [2] Ver biblioteca de descargas local                                    │
│    [3] Salir de Coda                                                        │
│                                                                             │
└───────────────────── Selecciona una opción del 1 al 3 ──────────────────────┘
```

---

## ⚙️ Requisitos Previos

1. **Python 3.10 o superior**.
2. **FFmpeg**: Necesario para la extracción y conversión a MP3.

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
Te permitirá navegar por el menú, buscar canciones, ingresar playlists o explorar tu biblioteca de archivos descargados.

### 2. Modo Directo por Argumentos (CLI)
Si prefieres descargar directamente desde la terminal:

- **Por nombre de canción**:
  ```bash
  python main.py "The Beatles - Yesterday"
  ```
- **Por URL de video**:
  ```bash
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  ```
- **Descargar Playlist (con límite de pistas)**:
  ```bash
  python main.py "https://www.youtube.com/playlist?list=PL..." -l 10
  ```
- **Carpeta de salida personalizada**:
  ```bash
  python main.py "Queen Bohemian Rhapsody" -o "./mi_musica"
  ```

---

## 🧪 Pruebas Unitarias

Para ejecutar la suite de pruebas automatizadas con `pytest`:
```bash
pytest tests/ -v
```

---

## 📁 Estructura del Proyecto

```text
coda/
├── core/
│   ├── downloader.py    # Orquestación con yt-dlp y conversión de audio
│   └── resolver.py      # Resolución y clasificación de consultas
├── metadata/
│   └── writer.py        # Tags ID3v2 y extracción de portadas APIC
├── ui/
│   ├── cli.py           # Parseo de argumentos con argparse
│   └── display.py       # Renderizado enriquecido en consola con Rich
├── utils/
│   ├── file_manager.py  # Sanitización de nombres de archivo
│   └── validator.py     # Detección y validación de URLs y playlists
├── tests/
│   ├── test_file_manager.py
│   └── test_validator.py
├── downloads/           # Directorio donde se guardan los archivos .mp3
├── config.py            # Configuraciones globales y logging
├── main.py              # Punto de entrada de la aplicación
├── requirements.txt     # Dependencias de producción
├── LICENSE              # Licencia MIT
└── README.md
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

Desarrollado con ❤️ por [@rosasjuancarlos006-ux](https://github.com/rosasjuancarlos006-ux).
