from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DownloadPhase(Enum):
    """Enumeration representing the operational phases of an audio download."""
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    METADATA = "metadata"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class ProgressEvent:
    """Immutable data transfer object carrying agnostic progress metrics to any view."""
    phase: DownloadPhase
    percentage: Optional[float] = None
    speed_bytes_sec: Optional[float] = None
    eta_seconds: Optional[int] = None
    current_item: Optional[int] = None
    total_items: Optional[int] = None
    item_title: Optional[str] = None
    message: Optional[str] = None


def create_progress_event(
    phase: DownloadPhase,
    percentage: Optional[float] = None,
    speed_bytes_sec: Optional[float] = None,
    eta_seconds: Optional[int] = None,
    current_item: Optional[int] = None,
    total_items: Optional[int] = None,
    item_title: Optional[str] = None,
    message: Optional[str] = None
) -> ProgressEvent:
    """
    Pure factory function that constructs and validates a ProgressEvent.
    Normalizes percentage to the range [0.0, 100.0] if provided.
    """
    normalized_percentage = percentage
    if normalized_percentage is not None:
        normalized_percentage = max(0.0, min(100.0, float(normalized_percentage)))

    return ProgressEvent(
        phase=phase,
        percentage=normalized_percentage,
        speed_bytes_sec=float(speed_bytes_sec) if speed_bytes_sec is not None else None,
        eta_seconds=int(eta_seconds) if eta_seconds is not None else None,
        current_item=int(current_item) if current_item is not None else None,
        total_items=int(total_items) if total_items is not None else None,
        item_title=str(item_title) if item_title is not None else None,
        message=str(message) if message is not None else None,
    )
