import time
from pathlib import Path
import pytest

from utils.validator import (
    classify_input,
    clean_mixed_url,
    clean_video_url,
    is_playlist_url,
    is_valid_youtube_url,
)
from utils.platform_validator import (
    DEFAULT_PLATFORM,
    PLATFORM_DISPLAY_NAMES,
    SUPPORTED_PLATFORMS,
    check_platform_mismatch,
    detect_url_platform,
    normalize_platform_input,
)
from utils.format_validator import (
    DEFAULT_FORMAT,
    SUPPORTED_FORMATS,
    is_valid_format,
    normalize_format_input,
    resolve_audio_format,
)
from utils.file_manager import (
    PARTIAL_EXTENSIONS,
    SUPPORTED_AUDIO_EXTENSIONS,
    AudioFileInfo,
    cleanup_files,
    find_partial_download_files,
    resolve_incremental_filename,
    sanitize_filename,
    scan_audio_downloads,
    scan_downloaded_audio_metadata,
)


# =====================================================================
# QA Test Suite: Módulos de Validación y Utilidades Puras (Tarea 1.1)
# =====================================================================


class TestValidatorCoreQA:
    """Pruebas exhaustivas de validación, clasificación y poda de URLs de YouTube."""

    def test_tc_1_1_1_clean_mixed_url_with_mixes_and_radios(self):
        """Poda de URLs con parámetros de mix/radio (list=RD..., list=UL...)."""
        # YouTube estándar con mix
        url_yt_mix = "https://www.youtube.com/watch?v=kJQP7kiw5Fk&list=RDkJQP7kiw5Fk&start_radio=1&index=1"
        clean_yt, was_pruned_yt = clean_mixed_url(url_yt_mix)
        assert clean_yt == "https://www.youtube.com/watch?v=kJQP7kiw5Fk"
        assert was_pruned_yt is True

        # YouTube Music con mix
        url_ytm_mix = "https://music.youtube.com/watch?v=hrcBnDALOQs&list=RDAMVMhrcBnDALOQs"
        clean_ytm, was_pruned_ytm = clean_mixed_url(url_ytm_mix)
        assert clean_ytm == "https://music.youtube.com/watch?v=hrcBnDALOQs"
        assert was_pruned_ytm is True

        # Video con múltiples parámetros innecesarios (&t=, &feature=, &si=)
        url_with_noise = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be&si=xyz123&list=RD123"
        clean_noise, was_pruned_noise = clean_mixed_url(url_with_noise)
        assert clean_noise == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert was_pruned_noise is True

    def test_tc_1_1_1_clean_mixed_url_preserves_pure_playlists(self):
        """No debe podar URLs de listas de reproducción legítimas /playlist?list=..."""
        pure_pl_yt = "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
        clean_pl_yt, was_pruned = clean_mixed_url(pure_pl_yt)
        assert clean_pl_yt == pure_pl_yt
        assert was_pruned is False

        pure_pl_ytm = "https://music.youtube.com/playlist?list=RDCLAK5uy_kfdxoj"
        clean_pl_ytm, was_pruned_ytm = clean_mixed_url(pure_pl_ytm)
        assert clean_pl_ytm == pure_pl_ytm
        assert was_pruned_ytm is False

    def test_tc_1_1_1_clean_mixed_url_edge_cases(self):
        """Casos límite: entradas vacías, tipos no cadena, URLs sin esquema."""
        assert clean_mixed_url("") == ("", False)
        assert clean_mixed_url(None) == ("", False)
        assert clean_mixed_url(12345) == ("", False)  # type: ignore
        assert clean_mixed_url("   ") == ("", False)

        # URL sin esquema HTTP/HTTPS explícito
        url_noscheme = "www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ"
        clean_noscheme, pruned = clean_mixed_url(url_noscheme)
        assert "v=dQw4w9WgXcQ" in clean_noscheme
        assert "list=" not in clean_noscheme
        assert pruned is True

        # clean_video_url wrapper debe retornar string consistente
        assert clean_video_url(url_yt_mix := "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RD123") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_tc_1_1_1_is_valid_youtube_url_rigorous(self):
        """Validación estricta de dominios y estructuras soportadas."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://music.youtube.com/playlist?list=PL123",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "music.youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        for url in valid_urls:
            assert is_valid_youtube_url(url) is True, f"Falló validando URL legítima: {url}"

        invalid_urls = [
            "",
            "   ",
            None,
            "https://spotify.com/track/4cOdK2wGLETKBW3PvgPWqT",
            "https://soundcloud.com/artist/track",
            "https://vimeo.com/76979871",
            "cancion de moda 2026",
            "http://notyoutube.com/watch?v=123",
            "https://music.youtube.com.attacker.com/watch?v=123",
        ]
        for url in invalid_urls:
            assert is_valid_youtube_url(url) is False, f"Aceptó erróneamente URL inválida: {url}"

    def test_tc_1_1_1_is_playlist_url_discrimination(self):
        """Discriminación exacta entre playlist pura y video individual con mix."""
        # Playlists puras
        assert is_playlist_url("https://www.youtube.com/playlist?list=PL123") is True
        assert is_playlist_url("https://music.youtube.com/playlist?list=PL123") is True
        assert is_playlist_url("www.youtube.com/playlist?list=PL123") is True

        # Videos individuales con parámetros de mix (NO son playlists puras)
        assert is_playlist_url("https://www.youtube.com/watch?v=123&list=RD123") is False
        assert is_playlist_url("https://music.youtube.com/watch?v=123&list=RD123") is False
        assert is_playlist_url("https://www.youtube.com/watch?feature=shared&v=123&list=PL123") is False

        # No playlists
        assert is_playlist_url("https://youtu.be/dQw4w9WgXcQ") is False
        assert is_playlist_url("texto de busqueda") is False
        assert is_playlist_url("") is False
        assert is_playlist_url(None) is False

    def test_tc_1_1_1_classify_input_taxonomy(self):
        """Taxonomía completa de clasificación: video, playlist, search."""
        assert classify_input("https://www.youtube.com/playlist?list=PL99") == "playlist"
        assert classify_input("https://music.youtube.com/playlist?list=PL99") == "playlist"

        assert classify_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "video"
        assert classify_input("https://youtu.be/dQw4w9WgXcQ") == "video"
        assert classify_input("https://music.youtube.com/watch?v=dQw4w9WgXcQ&list=RD123") == "video"

        assert classify_input("Imagine Dragons Believer") == "search"
        assert classify_input("   ") == "search"
        assert classify_input("") == "search"
        assert classify_input(None) == "search"


class TestPlatformValidatorCoreQA:
    """Pruebas exhaustivas para la selección, normalización y detección de plataformas."""

    def test_tc_1_1_2_constants_and_defaults(self):
        """Constantes oficiales del ecosistema de plataformas."""
        assert DEFAULT_PLATFORM == "youtube"
        assert SUPPORTED_PLATFORMS == ("youtube", "youtube_music")
        assert PLATFORM_DISPLAY_NAMES["youtube"] == "YouTube"
        assert PLATFORM_DISPLAY_NAMES["youtube_music"] == "YouTube Music"

    def test_tc_1_1_2_normalize_platform_input_aliases(self):
        """Normalización de alias numéricos y textuales con tolerancia a espacios."""
        # Alias YouTube
        for alias in ["1", "youtube", "yt", "YT", "  YouTube  ", "YOUTUBE"]:
            success, plat = normalize_platform_input(alias)
            assert success is True
            assert plat == "youtube"

        # Alias YouTube Music
        for alias in ["2", "music", "ytmusic", "YouTube Music", "yt_music", "youtube   music\t"]:
            success, plat = normalize_platform_input(alias)
            assert success is True
            assert plat == "youtube_music"

        # Defaults ante vacío
        for empty_val in ["", "   ", "\n\t", None]:
            success, plat = normalize_platform_input(empty_val)
            assert success is True
            assert plat == "youtube"

        # Entradas inválidas
        for invalid in ["3", "spotify", "apple", "soundcloud", "0", "-1"]:
            success, plat = normalize_platform_input(invalid)
            assert success is False
            assert plat is None

    def test_tc_1_1_2_detect_url_platform_precision(self):
        """Detección precisa de plataforma por dominio."""
        assert detect_url_platform("https://music.youtube.com/watch?v=abc") == "youtube_music"
        assert detect_url_platform("http://www.music.youtube.com/playlist?list=PL1") == "youtube_music"
        assert detect_url_platform("https://www.youtube.com/watch?v=abc") == "youtube"
        assert detect_url_platform("https://youtu.be/abc") == "youtube"
        assert detect_url_platform("http://youtube.com/shorts/123") == "youtube"

        # Dominios externos o no reconocidos
        assert detect_url_platform("https://spotify.com") is None
        assert detect_url_platform("busqueda libre de cancion") is None
        assert detect_url_platform("") is None
        assert detect_url_platform(None) is None

    def test_tc_1_1_2_check_platform_mismatch_adaptation(self):
        """Auto-adaptación ante discrepancias entre la selección del usuario y el enlace ingresado."""
        # Discrepancia real -> Requiere adaptación pedagógica
        mismatch, adapted = check_platform_mismatch("youtube", "https://music.youtube.com/watch?v=abc")
        assert mismatch is True
        assert adapted == "youtube_music"

        mismatch, adapted = check_platform_mismatch("youtube_music", "https://www.youtube.com/watch?v=abc")
        assert mismatch is True
        assert adapted == "youtube"

        mismatch, adapted = check_platform_mismatch("youtube_music", "https://youtu.be/abc")
        assert mismatch is True
        assert adapted == "youtube"

        # Sin discrepancia
        mismatch, adapted = check_platform_mismatch("youtube", "https://www.youtube.com/watch?v=abc")
        assert mismatch is False
        assert adapted == "youtube"

        mismatch, adapted = check_platform_mismatch("youtube_music", "https://music.youtube.com/watch?v=abc")
        assert mismatch is False
        assert adapted == "youtube_music"

        # Búsqueda por texto no causa discrepancia
        mismatch, adapted = check_platform_mismatch("youtube", "Queen Bohemian Rhapsody")
        assert mismatch is False
        assert adapted == "youtube"


class TestFormatValidatorCoreQA:
    """Pruebas exhaustivas para la normalización y resolución de formatos de audio."""

    def test_tc_1_1_3_format_constants(self):
        """Formatos permitidos y formato por defecto."""
        assert DEFAULT_FORMAT == "mp3"
        assert SUPPORTED_FORMATS == ("mp3", "m4a", "opus")

    def test_tc_1_1_3_normalize_format_input(self):
        """Limpieza y conversión a minúsculas."""
        assert normalize_format_input("MP3") == "mp3"
        assert normalize_format_input("  M4A  ") == "m4a"
        assert normalize_format_input("OpUs") == "opus"
        assert normalize_format_input("") == ""
        assert normalize_format_input("   ") == ""
        assert normalize_format_input(None) == ""
        assert normalize_format_input(123) == ""  # type: ignore

    def test_tc_1_1_3_is_valid_format_filtering(self):
        """Validación estricta de formatos soportados y rechazo de extensiones anómalas."""
        for fmt in ["mp3", "m4a", "opus"]:
            assert is_valid_format(fmt) is True

        for unsupp in ["flac", "wav", "aac", "ogg", "wma", "alac", "mp4", "320k", ""]:
            assert is_valid_format(unsupp) is False

        # Rechazo de longitud extrema (> 20 caracteres)
        assert is_valid_format("a" * 21) is False

    def test_tc_1_1_3_resolve_audio_format_lifecycle(self):
        """Resolución con fallback a MP3 ante entradas vacías o confirmación del formato."""
        # Vacíos o espacios -> MP3 por defecto
        assert resolve_audio_format("") == (True, "mp3")
        assert resolve_audio_format("   ") == (True, "mp3")
        assert resolve_audio_format(None) == (True, "mp3")

        # Formatos válidos explícitos
        assert resolve_audio_format("mp3") == (True, "mp3")
        assert resolve_audio_format("M4A") == (True, "m4a")
        assert resolve_audio_format("  opus  ") == (True, "opus")

        # Formatos no soportados
        assert resolve_audio_format("wav") == (False, "")
        assert resolve_audio_format("flac") == (False, "")
        assert resolve_audio_format("desconocido") == (False, "")


class TestFileManagerCoreQA:
    """Pruebas exhaustivas para sanitización, colisiones de archivos y gestión de biblioteca."""

    def test_tc_1_1_4_sanitize_filename_windows_reserved(self):
        """Sanitización estricta de los 9 caracteres prohibidos en Windows: < > : " / \\ | ? *"""
        forbidden_chars = '<>:"/\\|?*'
        sample_title = f'Artista{forbidden_chars[0]}Titulo{forbidden_chars[1]}Cancion{forbidden_chars[2]}Test'
        sanitized = sanitize_filename(sample_title)
        
        for char in forbidden_chars:
            assert char not in sanitized, f"Caracter prohibido '{char}' no fue saneado: {sanitized}"

        # Caracteres válidos preservados (Unicode, tildes, corchetes, guiones)
        unicode_title = "Rosalía & Rauw Alejandro - BESO [Official Audio] (2023)"
        assert sanitize_filename(unicode_title) == unicode_title

        # Espacios al inicio y fin eliminados
        assert sanitize_filename("   Cancion con espacios   ") == "Cancion con espacios"

    def test_tc_1_1_4_resolve_incremental_filename_collisions(self, tmp_path: Path):
        """Resolución incremental de nombres ante colisiones en disco."""
        # 1. Sin colisión previa
        p1 = resolve_incremental_filename(tmp_path, "Cancion", "mp3")
        assert p1 == tmp_path / "Cancion.mp3"
        p1.touch()

        # 2. Primera colisión -> genera (1)
        p2 = resolve_incremental_filename(tmp_path, "Cancion", "mp3")
        assert p2 == tmp_path / "Cancion (1).mp3"
        p2.touch()

        # 3. Segunda colisión -> genera (2)
        p3 = resolve_incremental_filename(tmp_path, "Cancion", "mp3")
        assert p3 == tmp_path / "Cancion (2).mp3"
        p3.touch()

        # 4. Tercera colisión -> genera (3)
        p4 = resolve_incremental_filename(tmp_path, "Cancion", "mp3")
        assert p4 == tmp_path / "Cancion (3).mp3"

        # 5. Soporte de extensión con o sin punto inicial
        p_m4a = resolve_incremental_filename(tmp_path, "Track", ".m4a")
        assert p_m4a.name == "Track.m4a"

        p_opus = resolve_incremental_filename(tmp_path, "Track", "opus")
        assert p_opus.name == "Track.opus"

        # 6. Fallback a 'audio' si el título queda vacío tras saneamiento
        p_empty = resolve_incremental_filename(tmp_path, '   :::***???///   ', "mp3")
        assert "audio" in p_empty.name

    def test_tc_1_1_4_scan_downloaded_audio_metadata_and_downloads(self, tmp_path: Path):
        """Escaneo de biblioteca, filtrado de extensiones y ordenamiento cronológico descendente."""
        # Crear archivos con marcas de tiempo distintas
        f1 = tmp_path / "pista_antigua.mp3"
        f1.write_bytes(b"A" * 500)
        time.sleep(0.02)

        f2 = tmp_path / "pista_media.opus"
        f2.write_bytes(b"B" * (1024 * 512))  # 512 KB
        time.sleep(0.02)

        f3 = tmp_path / "pista_nueva.m4a"
        f3.write_bytes(b"C" * (1024 * 1024 * 3))  # 3 MB

        # Archivos no soportados o temporales que DEBEN ser ignorados
        (tmp_path / "cover.jpg").write_bytes(b"image")
        (tmp_path / "metadata.json").write_bytes(b"{}")
        (tmp_path / "download.mp3.part").write_bytes(b"partial")

        # Escaneo estructurado para GUI (scan_downloaded_audio_metadata)
        meta_items = scan_downloaded_audio_metadata(tmp_path)
        assert len(meta_items) == 3
        # Debe estar ordenado de más reciente a más antiguo
        assert meta_items[0]["name"] == "pista_nueva.m4a"
        assert meta_items[0]["format"] == "M4A"
        assert "MB" in meta_items[0]["size_str"]
        assert meta_items[1]["name"] == "pista_media.opus"
        assert "KB" in meta_items[1]["size_str"]
        assert meta_items[2]["name"] == "pista_antigua.mp3"
        assert "B" in meta_items[2]["size_str"]

        # Escaneo de dataclasses (scan_audio_downloads)
        audio_info_items = scan_audio_downloads(tmp_path)
        assert len(audio_info_items) == 3
        assert audio_info_items[0].name == "pista_nueva.m4a"
        assert isinstance(audio_info_items[0], AudioFileInfo)

    def test_tc_1_1_4_find_partial_download_files_and_cleanup(self, tmp_path: Path):
        """Detección y purga segura de temporales (.part, .ytdl, etc.) generados durante una descarga."""
        # Archivo previo a la descarga
        old_file = tmp_path / "previo.mp3"
        old_file.write_bytes(b"ok")
        time.sleep(0.05)

        start_timestamp = time.time()
        time.sleep(0.05)

        # Archivos temporales generados durante la descarga
        temp1 = tmp_path / "cancion.mp3.part"
        temp1.write_bytes(b"chunk1")
        temp2 = tmp_path / "stream.ytdl"
        temp2.write_bytes(b"chunk2")
        temp3 = tmp_path / "interrupted.opus"
        temp3.write_bytes(b"chunk3")

        partials = find_partial_download_files(tmp_path, start_timestamp)
        partial_names = {p.name for p in partials}
        assert "cancion.mp3.part" in partial_names
        assert "stream.ytdl" in partial_names
        assert "interrupted.opus" in partial_names
        assert "previo.mp3" not in partial_names

        # Purga segura mediante cleanup_files
        deleted_count = cleanup_files(partials)
        assert deleted_count == 3
        assert not temp1.exists()
        assert not temp2.exists()
        assert not temp3.exists()
        assert old_file.exists(), "No debe eliminar archivos previos al inicio de la descarga"

        # Tolerancia ante archivos que no existen
        non_existent = [tmp_path / "fantasma.part", tmp_path / "no_existe.ytdl"]
        assert cleanup_files(non_existent) == 0
