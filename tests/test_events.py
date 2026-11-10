import pytest
from core.events import DownloadPhase, ProgressEvent, create_progress_event

class TestEvents:
    def test_download_phase_enum_values(self):
        """Verifica que DownloadPhase contenga todas las fases requeridas."""
        expected_phases = {
            "preparing", "downloading", "converting",
            "metadata", "completed", "error"
        }
        actual_phases = {phase.value for phase in DownloadPhase}
        assert actual_phases == expected_phases

    def test_progress_event_defaults(self):
        """Verifica que ProgressEvent inicialice con valores por defecto opcionales."""
        event = ProgressEvent(phase=DownloadPhase.PREPARING)
        assert event.phase == DownloadPhase.PREPARING
        assert event.percentage is None
        assert event.speed_bytes_sec is None
        assert event.eta_seconds is None
        assert event.current_item is None
        assert event.total_items is None
        assert event.item_title is None
        assert event.message is None

    def test_progress_event_immutability(self):
        """Verifica que ProgressEvent sea inmutable (frozen dataclass)."""
        event = ProgressEvent(phase=DownloadPhase.DOWNLOADING, percentage=50.0)
        with pytest.raises((AttributeError, TypeError)):
            event.percentage = 75.0  # type: ignore

    def test_create_progress_event_factory(self):
        """Verifica la función helper create_progress_event."""
        event = create_progress_event(
            phase=DownloadPhase.DOWNLOADING,
            percentage=45.5,
            speed_bytes_sec=1024 * 1024,
            eta_seconds=12,
            current_item=1,
            total_items=5,
            item_title="Canción de Prueba",
            message="Descargando audio"
        )
        assert isinstance(event, ProgressEvent)
        assert event.phase == DownloadPhase.DOWNLOADING
        assert event.percentage == 45.5
        assert event.speed_bytes_sec == 1048576.0
        assert event.eta_seconds == 12
        assert event.current_item == 1
        assert event.total_items == 5
        assert event.item_title == "Canción de Prueba"
        assert event.message == "Descargando audio"

    def test_create_progress_event_clamping(self):
        """Verifica que los porcentajes fuera de rango sean normalizados entre 0.0 y 100.0."""
        event_over = create_progress_event(phase=DownloadPhase.DOWNLOADING, percentage=150.0)
        assert event_over.percentage == 100.0

        event_under = create_progress_event(phase=DownloadPhase.DOWNLOADING, percentage=-10.0)
        assert event_under.percentage == 0.0
