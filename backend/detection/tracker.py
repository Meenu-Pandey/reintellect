"""
ByteTrack wrapper for multi-object tracking.

Wraps the ByteTrack implementation from ultralytics to provide
persistent track IDs across frames.

Re-association window: lost tracks re-associated if absent < 30 frames;
new track_id assigned after >= 30 frames of absence.
"""

from __future__ import annotations

import numpy as np
from ultralytics.trackers.byte_tracker import BYTETracker, STrack
from ultralytics.utils import IterableSimpleNamespace


class _DetectionResults:
    """Lightweight wrapper that mimics ultralytics Results interface for ByteTrack.

    ByteTrack expects an object with .conf, .cls, .xywh, .xyxy attributes
    and supports indexing.
    """

    def __init__(self, xyxy: np.ndarray, conf: np.ndarray, cls: np.ndarray) -> None:
        self._xyxy = xyxy
        self._conf = conf
        self._cls = cls

    @property
    def xyxy(self) -> np.ndarray:
        return self._xyxy

    @property
    def conf(self) -> np.ndarray:
        return self._conf

    @property
    def cls(self) -> np.ndarray:
        return self._cls

    @property
    def xywh(self) -> np.ndarray:
        """Convert xyxy to xywh format."""
        if len(self._xyxy) == 0:
            return np.empty((0, 4), dtype=np.float32)
        x1 = self._xyxy[:, 0]
        y1 = self._xyxy[:, 1]
        x2 = self._xyxy[:, 2]
        y2 = self._xyxy[:, 3]
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = x2 - x1
        h = y2 - y1
        return np.column_stack([cx, cy, w, h])

    def __len__(self) -> int:
        return len(self._xyxy)

    def __getitem__(self, idx):
        return _DetectionResults(
            xyxy=self._xyxy[idx],
            conf=self._conf[idx],
            cls=self._cls[idx],
        )


class ByteTrackWrapper:
    """Wraps ultralytics ByteTrack for person tracking.

    Attributes:
        max_lost_frames: Number of frames a track can be lost before
            being considered gone (re-association window).
    """

    def __init__(self, max_lost_frames: int = 30, fps: float = 30.0) -> None:
        """Initialise ByteTrack with re-association window config.

        Args:
            max_lost_frames: Lost tracks re-associated if absent < this many
                frames; new track_id assigned after >= this many frames.
            fps: Frame rate used for internal buffer calculations.
        """
        self.max_lost_frames = max_lost_frames
        self._fps = fps

        # ByteTrack's internal buffer has a +2 offset between track_buffer and
        # the actual frame count at which a track is dropped. Compensate so that
        # the public API contract holds: new ID at >= max_lost_frames.
        internal_buffer = max(1, max_lost_frames - 2)

        # Configure ByteTrack args matching ultralytics expected interface
        args = IterableSimpleNamespace(
            track_high_thresh=0.25,
            track_low_thresh=0.1,
            new_track_thresh=0.25,
            track_buffer=internal_buffer,
            match_thresh=0.8,
            fuse_score=True,
        )
        self._tracker = BYTETracker(args, frame_rate=int(fps))

    def update(self, detections: list[dict]) -> list[dict]:
        """Accept raw YOLO detections and return tracked detections with track_id.

        Args:
            detections: List of dicts with keys:
                - bbox: (x1, y1, x2, y2) normalised coordinates [0.0, 1.0]
                - confidence: float in [0.0, 1.0]
                - class_id: int (typically 0 for person)

        Returns:
            List of dicts with keys:
                - track_id: int (persistent across frames)
                - bbox: (x1, y1, x2, y2) normalised coordinates
                - confidence: float
        """
        if not detections:
            # Pass empty results to keep tracker state updated
            empty_results = _DetectionResults(
                xyxy=np.empty((0, 4), dtype=np.float32),
                conf=np.empty((0,), dtype=np.float32),
                cls=np.empty((0,), dtype=np.float32),
            )
            self._tracker.update(empty_results)
            return []

        # Build arrays for the tracker
        # Scale normalised coords to virtual 1000x1000 pixel space
        n = len(detections)
        xyxy = np.zeros((n, 4), dtype=np.float32)
        conf = np.zeros((n,), dtype=np.float32)
        cls = np.zeros((n,), dtype=np.float32)

        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]
            xyxy[i] = [x1 * 1000.0, y1 * 1000.0, x2 * 1000.0, y2 * 1000.0]
            conf[i] = det["confidence"]
            cls[i] = det.get("class_id", 0)

        results_obj = _DetectionResults(xyxy=xyxy, conf=conf, cls=cls)

        # Update tracker
        tracked_output = self._tracker.update(results_obj)

        # tracked_output is an np.ndarray with shape (N, 7) or similar
        # containing [x1, y1, x2, y2, track_id, conf, cls] or access via STrack
        output = []

        # The return from update in newer ultralytics is an ndarray
        if isinstance(tracked_output, np.ndarray) and tracked_output.size > 0:
            for row in tracked_output:
                # Format: [x1, y1, x2, y2, track_id, conf, cls]
                if len(row) >= 6:
                    output.append(
                        {
                            "track_id": int(row[4]),
                            "bbox": (
                                float(row[0] / 1000.0),
                                float(row[1] / 1000.0),
                                float(row[2] / 1000.0),
                                float(row[3] / 1000.0),
                            ),
                            "confidence": float(row[5]),
                        }
                    )
        elif hasattr(tracked_output, '__iter__') and not isinstance(tracked_output, np.ndarray):
            # Fallback: list of STrack objects
            for track in tracked_output:
                tlbr = track.xyxy if hasattr(track, 'xyxy') else track.tlbr
                output.append(
                    {
                        "track_id": int(track.track_id),
                        "bbox": (
                            float(tlbr[0] / 1000.0),
                            float(tlbr[1] / 1000.0),
                            float(tlbr[2] / 1000.0),
                            float(tlbr[3] / 1000.0),
                        ),
                        "confidence": float(track.score),
                    }
                )

        return output

    def reset(self) -> None:
        """Reset the tracker state (all tracks lost)."""
        internal_buffer = max(1, self.max_lost_frames - 2)
        args = IterableSimpleNamespace(
            track_high_thresh=0.25,
            track_low_thresh=0.1,
            new_track_thresh=0.25,
            track_buffer=internal_buffer,
            match_thresh=0.8,
            fuse_score=True,
        )
        self._tracker = BYTETracker(args, frame_rate=int(self._fps))
