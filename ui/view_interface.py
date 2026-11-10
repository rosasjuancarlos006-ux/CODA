from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from core.events import ProgressEvent
from utils.file_manager import AudioFileInfo


@runtime_checkable
class ViewInterface(Protocol):
    """
    Abstract presentation contract defining the interface that any Coda view
    (terminal, GUI, web, or testing mock) must satisfy to interact with the controller.
    """

    def show_banner(self) -> None:
        """Render the welcome banner."""
        ...

    def show_main_menu(self) -> str:
        """Display the primary interactive options and return the user's choice."""
        ...

    def prompt_platform(self) -> str:
        """Prompt user for target platform ('youtube' or 'youtube_music')."""
        ...

    def prompt_query(self, platform_name: str) -> str:
        """Prompt user for search terms or resource URL."""
        ...

    def prompt_playlist_limit(self) -> Optional[int]:
        """Prompt user for download track limit for playlists (None = all)."""
        ...

    def prompt_audio_format(self, is_playlist: bool) -> str:
        """Prompt user for desired audio format ('mp3', 'm4a', 'opus')."""
        ...

    def show_platform_mismatch(self, selected: str, adapted: str) -> None:
        """Display pedagogical notification of platform auto-adaptation."""
        ...

    def show_info(self, message: str) -> None:
        """Display informational notification."""
        ...

    def show_warning(self, message: str) -> None:
        """Display warning notification."""
        ...

    def show_error(self, message: str, error_type: Optional[str] = None) -> None:
        """Display error notification with optional error categorization."""
        ...

    def show_single_success(self, result: Dict[str, Any]) -> None:
        """Display aesthetic completion summary for an individual track download."""
        ...

    def show_playlist_summary(self, summary: Dict[str, Any], output_dir: Path) -> None:
        """Display table/panel summary for an entire playlist download."""
        ...

    def show_downloads_table(self, downloads: List[AudioFileInfo]) -> None:
        """Render structured table displaying locally downloaded audio tracks."""
        ...

    def show_empty_downloads(self) -> None:
        """Display friendly notification when no downloaded tracks exist."""
        ...

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle incoming progress event and update presentation accordingly."""
        ...

    def start_progress_task(self, title: str, total: Optional[int] = None) -> None:
        """Initiate or activate a long-running progress visualization task."""
        ...

    def stop_progress_task(self) -> None:
        """Conclude and dismiss any active progress visualization."""
        ...
