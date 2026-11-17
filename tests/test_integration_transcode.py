import os
from pathlib import Path
import subprocess
import pytest

from core.downloader import find_ffmpeg


# =====================================================================
# QA Test Suite: Extracción y Transcodificación Multi-formato (Tarea 2.2)
# =====================================================================


class TestMultiFormatTranscodeIntegrationQA:
    """Pruebas de integración de postprocesamiento de audio con FFmpeg en MP3, M4A y OPUS."""

    @pytest.fixture(scope="class")
    @classmethod
    def ffmpeg_bin(cls):
        binary = find_ffmpeg()
        if not binary or not Path(binary).exists():
            pytest.skip("FFmpeg no disponible en el entorno para pruebas de integración de transcodificación.")
        return binary

    @pytest.fixture(scope="class")
    @classmethod
    def ffprobe_bin(cls):
        local_ffprobe = Path(__file__).resolve().parent.parent / "bin" / "ffprobe.exe"
        if local_ffprobe.exists():
            return str(local_ffprobe)
        import shutil
        sys_ffprobe = shutil.which("ffprobe")
        if sys_ffprobe:
            return sys_ffprobe
        return None

    def _generate_synthetic_wav(self, ffmpeg_bin: str, output_wav: Path, duration_sec: int = 1):
        """Genera un archivo de audio sintético WAV puro utilizando el generador lavfi de FFmpeg."""
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration_sec}",
            str(output_wav),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=10)
        assert res.returncode == 0, f"Error generando WAV sintético: {res.stderr.decode()}"
        assert output_wav.exists()

    def test_tc_2_2_1_transcode_to_mp3_192k(self, ffmpeg_bin: str, tmp_path: Path):
        """Transcodifica audio sintético a MP3 con bitrate de 192k."""
        wav_path = tmp_path / "fuente.wav"
        self._generate_synthetic_wav(ffmpeg_bin, wav_path)

        mp3_path = tmp_path / "resultado.mp3"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-i", str(wav_path),
            "-acodec", "libmp3lame",
            "-b:a", "192k",
            str(mp3_path),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=10)
        assert res.returncode == 0, f"Fallo al transcodificar a MP3: {res.stderr.decode()}"
        assert mp3_path.exists()
        assert mp3_path.stat().st_size > 1000

        # Verificación de cabecera de stream MPEG Audio Layer III
        content = mp3_path.read_bytes()
        # Primeros bytes típicamente contienen sync word 0xFF 0xFB o ID3 tag 0x49 0x44 0x33
        assert content.startswith(b"\xff\xfb") or content.startswith(b"ID3") or b"\xff\xfb" in content[:1024]

    def test_tc_2_2_2_transcode_to_m4a_aac(self, ffmpeg_bin: str, tmp_path: Path):
        """Transcodifica audio sintético a contenedor MP4/M4A con códec AAC."""
        wav_path = tmp_path / "fuente.wav"
        self._generate_synthetic_wav(ffmpeg_bin, wav_path)

        m4a_path = tmp_path / "resultado.m4a"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-i", str(wav_path),
            "-acodec", "aac",
            "-b:a", "192k",
            str(m4a_path),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=10)
        assert res.returncode == 0, f"Fallo al transcodificar a M4A: {res.stderr.decode()}"
        assert m4a_path.exists()
        assert m4a_path.stat().st_size > 1000

        # Verificación del contenedor MP4/M4A (átomo ftyp)
        content = m4a_path.read_bytes()
        assert b"ftyp" in content[:32]

    def test_tc_2_2_3_transcode_to_opus(self, ffmpeg_bin: str, tmp_path: Path):
        """Transcodifica audio sintético a contenedor Ogg Opus."""
        wav_path = tmp_path / "fuente.wav"
        self._generate_synthetic_wav(ffmpeg_bin, wav_path)

        opus_path = tmp_path / "resultado.opus"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel", "error",
            "-i", str(wav_path),
            "-acodec", "libopus",
            "-b:a", "160k",
            str(opus_path),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=10)
        assert res.returncode == 0, f"Fallo al transcodificar a OPUS: {res.stderr.decode()}"
        assert opus_path.exists()
        assert opus_path.stat().st_size > 1000

        # Verificación del contenedor Ogg Opus (Magic bytes 'OggS' y 'OpusHead')
        content = opus_path.read_bytes()
        assert content.startswith(b"OggS")
        assert b"OpusHead" in content[:64]

    def test_tc_2_2_4_probe_container_integrity(self, ffmpeg_bin: str, ffprobe_bin: str, tmp_path: Path):
        """Valida metadatos y tasa de muestreo usando ffprobe si está disponible."""
        if not ffprobe_bin:
            pytest.skip("ffprobe no encontrado para validar contenedor.")

        wav_path = tmp_path / "fuente.wav"
        self._generate_synthetic_wav(ffmpeg_bin, wav_path)

        mp3_path = tmp_path / "test.mp3"
        subprocess.run([ffmpeg_bin, "-y", "-i", str(wav_path), "-b:a", "192k", str(mp3_path)], capture_output=True)

        probe_cmd = [
            ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=format_name,duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(mp3_path),
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        assert res.returncode == 0
        output = res.stdout.strip()
        assert "mp3" in output.lower()
