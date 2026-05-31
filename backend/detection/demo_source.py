"""
Demo video source for offline testing.

Loops a video clip indefinitely using cv2.VideoCapture.
When EOF is reached, seeks back to frame 0 and continues.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Generator

import cv2
import numpy as np


# Default path to the Purplle store footage
DEFAULT_CLIP_PATH = Path(__file__).resolve().parent.parent.parent / "resources" / "CAM 1.mp4"


class DemoVideoSource:
    """Loops a video clip indefinitely at the clip's native FPS.

    Attributes:
        clip_path: Path to the video file.
        fps: Frames per second of the source clip.
    """

    def __init__(self, clip_path: str | Path | None = None) -> None:
        self._clip_path = Path(clip_path) if clip_path else DEFAULT_CLIP_PATH
        if not self._clip_path.exists():
            raise FileNotFoundError(
                f"Video clip not found: {self._clip_path}"
            )

        self._cap = cv2.VideoCapture(str(self._clip_path))
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Failed to open video: {self._clip_path}"
            )

        self.fps: float = self._cap.get(cv2.CAP_PROP_FPS) or 30.0

    def frames(self) -> Generator[np.ndarray, None, None]:
        """Yield frames indefinitely, looping on EOF.

        Yields:
            BGR numpy array for each frame.
        """
        frame_interval = 1.0 / self.fps

        while True:
            last_time = time.perf_counter()

            ret, frame = self._cap.read()

            if not ret:
                # EOF reached — seek to frame 0 and continue
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
                if not ret:
                    raise RuntimeError(
                        f"Failed to read frame after seek: {self._clip_path}"
                    )

            yield frame

            # Pace to native FPS
            elapsed = time.perf_counter() - last_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def release(self) -> None:
        """Release the underlying VideoCapture resource."""
        if self._cap is not None:
            self._cap.release()

    def __del__(self) -> None:
        self.release()
