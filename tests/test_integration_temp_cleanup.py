from pathlib import Path
import time
import pytest

from utils.file_manager import cleanup_files, find_partial_download_files, sanitize_filename


# =====================================================================
# QA Test Suite: Rutas Windows y Poda de Temporales (Tarea 2.4)
# =====================================================================


class TestWindowsPathsAndTempCleanupQA:
    """
    Pruebas exhaustivas para gestión de rutas con espacios, tildes y caracteres
    Unicode en Windows, así como purga atómica de archivos temporales (.part, .ytdl, etc.).
    """

    def test_tc_2_4_1_windows_unicode_and_complex_paths(self, tmp_path: Path):
        """
        Verifica que se puedan crear, identificar y manipular archivos con rutas
        complejas en Windows que contengan tildes, caracteres cirílicos, asiáticos y espacios.
        """
        # Directorio con caracteres especiales y espacios
        complex_dir = tmp_path / "Descargas Coda (Música) — Año 2026 [Colección]"
        complex_dir.mkdir(parents=True, exist_ok=True)

        # Nombres de pista complejos
        track_names = [
            "01. Rosalía & Rauw Alejandro — BESO.mp3",
            "02. Кino - Группа крови (Audio).m4a",
            "03. 宇多田ヒカル - First Love (Remastered).opus",
            "04. Título con espacios múltiples    y símbolos #!.mp3",
        ]

        created_paths: list[Path] = []
        for name in track_names:
            sanitized = sanitize_filename(name)
            p = complex_dir / sanitized
            p.write_bytes(b"DUMMY_AUDIO_DATA")
            assert p.exists(), f"Fallo al escribir archivo en ruta Windows: {p}"
            created_paths.append(p)

        assert len(created_paths) == 4

        # Limpieza de los archivos creados
        deleted = cleanup_files(created_paths)
        assert deleted == 4
        for p in created_paths:
            assert not p.exists()

    def test_tc_2_4_2_purge_atomic_of_all_partial_extensions(self, tmp_path: Path):
        """
        Verifica la detección y purga atómica de todas las extensiones temporales
        reconocidas (.part, .ytdl, .temp, .tmp) respetando la marca de tiempo de inicio.
        """
        # 1. Archivo histórico que NO debe ser purgado
        historical_file = tmp_path / "archivo_historico.part"
        historical_file.write_text("antiguo")
        time.sleep(0.05)

        start_time = time.time()
        time.sleep(0.05)

        # 2. Archivos temporales generados a partir de start_time
        temp_files = [
            tmp_path / "descarga.mp3.part",
            tmp_path / "stream.ytdl",
            tmp_path / "transcode.temp",
            tmp_path / "chunk.tmp",
            tmp_path / "incompleto.mp3",  # Archivo de audio generado en la sesión
        ]
        for f in temp_files:
            f.write_text("datos temporales")

        # Detección
        detected_partials = find_partial_download_files(tmp_path, start_time)
        detected_names = {p.name for p in detected_partials}

        for f in temp_files:
            assert f.name in detected_names, f"No detectó archivo temporal: {f.name}"

        assert historical_file.name not in detected_names, "Detectó erróneamente un archivo previo al inicio de descarga."

        # Purga
        cleaned_count = cleanup_files(detected_partials)
        assert cleaned_count == len(temp_files)

        for f in temp_files:
            assert not f.exists(), f"El temporal {f.name} no fue purgado."

        assert historical_file.exists(), "El archivo histórico fue eliminado indebidamente."

    def test_tc_2_4_2_cleanup_files_resilience_to_errors(self, tmp_path: Path):
        """
        Verifica que cleanup_files tolere archivos ya borrados, listas vacías
        o rutas inaccesibles sin propagar excepciones al hilo de ejecución.
        """
        # Lista vacía
        assert cleanup_files([]) == 0

        # Archivos inexistentes
        ghosts = [tmp_path / "fantasma1.part", tmp_path / "fantasma2.ytdl"]
        assert cleanup_files(ghosts) == 0

        # Mezcla de existentes y no existentes
        real_file = tmp_path / "real.part"
        real_file.touch()
        assert cleanup_files([real_file, tmp_path / "inexistente.part"]) == 1
        assert not real_file.exists()
