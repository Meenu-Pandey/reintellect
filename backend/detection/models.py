"""
Detection pipeline data models.

These are internal pipeline models. `track_id` is a ByteTrack-internal concept
and is never exposed in the public event schema (which uses `visitor_id`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class TrackDetection:
    """A single person detection with tracking information.

    Attributes:
        track_id: ByteTrack-assigned persistent ID (internal only).
        bbox: Normalised bounding box (x1, y1, x2, y2) in [0.0, 1.0].
        confidence: Detection confidence score in [0.0, 1.0].
        role: Whether this detection is a visitor or staff member.
    """

    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float
    role: Literal["visitor", "staff"]

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        for i, val in enumerate(self.bbox):
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"bbox[{i}] must be in [0.0, 1.0], got {val}"
                )


@dataclass
class TrackFrame:
    """A single processed frame containing all tracked detections.

    Attributes:
        camera_id: Identifier of the source camera (e.g. "CAM1", "CAM3").
        frame_id: Sequential frame number within the camera feed.
        timestamp: UTC timestamp of frame capture.
        detections: List of tracked person detections in this frame.
    """

    camera_id: str
    frame_id: int
    timestamp: datetime
    detections: list[TrackDetection] = field(default_factory=list)
