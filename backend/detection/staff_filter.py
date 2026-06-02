"""
Staff filter using colour-based heuristic classification.

Classifies detections as "visitor" or "staff" based on the proportion
of a configured staff uniform colour (HSV range) within the bounding box.
"""

from __future__ import annotations

from typing import Literal

import cv2
import numpy as np


# Default staff colour config (dark purple/maroon Purplle uniform)
DEFAULT_STAFF_COLOUR_CONFIG: dict = {
    "hsv_lower": [140, 50, 50],   # Lower bound of staff uniform colour in HSV
    "hsv_upper": [170, 255, 255], # Upper bound of staff uniform colour in HSV
    "threshold": 0.15,            # Proportion of pixels that must match
}


class StaffFilter:
    """Classifies detections as visitor or staff using colour heuristic.

    The filter checks if the bounding box region contains a high proportion
    of a configured staff uniform colour (HSV range). If the proportion
    exceeds the threshold, the detection is classified as "staff".
    """

    def __init__(self, config: dict | None = None) -> None:
        """Initialise with staff colour configuration.

        Args:
            config: Dict with keys:
                - hsv_lower: [H, S, V] lower bound for staff colour
                - hsv_upper: [H, S, V] upper bound for staff colour
                - threshold: float proportion (0.0-1.0) to classify as staff
        """
        cfg = config or DEFAULT_STAFF_COLOUR_CONFIG
        self._hsv_lower = np.array(cfg["hsv_lower"], dtype=np.uint8)
        self._hsv_upper = np.array(cfg["hsv_upper"], dtype=np.uint8)
        self._threshold = float(cfg.get("threshold", 0.15))

    def classify(
        self,
        bbox: tuple[float, float, float, float],
        frame: np.ndarray,
        config: dict | None = None,
    ) -> Literal["visitor", "staff"]:
        """Classify a detection as visitor or staff based on colour.

        Args:
            bbox: Normalised bounding box (x1, y1, x2, y2) in [0.0, 1.0].
            frame: BGR numpy array of the full frame.
            config: Optional override config with hsv_lower, hsv_upper, threshold.

        Returns:
            "staff" if the bbox region contains >= threshold proportion of
            the configured staff colour, "visitor" otherwise.
        """
        if config is not None:
            hsv_lower = np.array(config["hsv_lower"], dtype=np.uint8)
            hsv_upper = np.array(config["hsv_upper"], dtype=np.uint8)
            threshold = float(config.get("threshold", self._threshold))
        else:
            hsv_lower = self._hsv_lower
            hsv_upper = self._hsv_upper
            threshold = self._threshold

        h, w = frame.shape[:2]

        # Convert normalised bbox to pixel coordinates
        x1 = max(0, int(bbox[0] * w))
        y1 = max(0, int(bbox[1] * h))
        x2 = min(w, int(bbox[2] * w))
        y2 = min(h, int(bbox[3] * h))

        # Guard against degenerate bboxes
        if x2 <= x1 or y2 <= y1:
            return "visitor"

        # Extract the region of interest
        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return "visitor"

        # Convert to HSV colour space
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Create mask for staff colour range
        mask = cv2.inRange(hsv_roi, hsv_lower, hsv_upper)

        # Calculate proportion of matching pixels
        total_pixels = mask.shape[0] * mask.shape[1]
        if total_pixels == 0:
            return "visitor"

        matching_pixels = np.count_nonzero(mask)
        proportion = matching_pixels / total_pixels

        if proportion >= threshold:
            return "staff"

        return "visitor"
