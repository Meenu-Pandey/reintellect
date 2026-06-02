"""Detection package."""

from detection.models import TrackDetection, TrackFrame
from detection.tracker import ByteTrackWrapper
from detection.staff_filter import StaffFilter
from detection.pipeline import DetectionPipeline

__all__ = [
    "TrackDetection",
    "TrackFrame",
    "ByteTrackWrapper",
    "StaffFilter",
    "DetectionPipeline",
]
