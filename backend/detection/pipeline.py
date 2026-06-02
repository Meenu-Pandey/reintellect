"""
Detection pipeline: YOLOv8 + ByteTrack + Staff Filter.

Reads frames from a video source, runs YOLOv8n inference (person class only),
applies ByteTrack for persistent tracking, classifies staff vs visitor,
and emits TrackFrame objects onto an asyncio.Queue.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np
import torch
from ultralytics import YOLO

from detection.models import TrackDetection, TrackFrame
from detection.staff_filter import StaffFilter
from detection.tracker import ByteTrackWrapper

logger = logging.getLogger(__name__)

# YOLO person class ID
_PERSON_CLASS_ID = 0

# Minimum detection thresholds
_MIN_CONFIDENCE = 0.5
_MIN_BBOX_HEIGHT_PX = 50


class DetectionPipeline:
    """YOLOv8 + ByteTrack detection pipeline.

    Reads frames from a video source, runs person detection, applies tracking,
    filters by confidence/size thresholds, classifies staff, and puts
    TrackFrame objects onto the track_queue for downstream consumption.

    Args:
        video_source: Object with a `frames()` generator yielding BGR numpy arrays
            and a `fps` attribute.
        track_queue: asyncio.Queue to publish TrackFrame objects to.
        config: Pipeline configuration dict with keys:
            - camera_id: str (e.g. "CAM1")
            - staff_colour: dict with hsv_lower, hsv_upper, threshold
            - confidence_threshold: float (default 0.5)
            - min_bbox_height_px: int (default 50)
            - max_lost_frames: int (default 30)
            - reconnect_interval: float (default 2.0)
    """

    def __init__(
        self,
        video_source: Any,
        track_queue: asyncio.Queue,
        config: dict,
    ) -> None:
        self._video_source = video_source
        self._track_queue = track_queue
        self._config = config

        self._camera_id: str = config.get("camera_id", "CAM1")
        self._confidence_threshold: float = config.get(
            "confidence_threshold", _MIN_CONFIDENCE
        )
        self._min_bbox_height_px: int = config.get(
            "min_bbox_height_px", _MIN_BBOX_HEIGHT_PX
        )
        self._reconnect_interval: float = config.get("reconnect_interval", 2.0)

        # Select device
        if torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        logger.info(
            "DetectionPipeline [%s] using device: %s", self._camera_id, self._device
        )

        # Initialise YOLO model (person detection)
        self._model = YOLO("yolov8n.pt")

        # Initialise ByteTrack wrapper
        fps = getattr(video_source, "fps", 30.0)
        max_lost_frames = config.get("max_lost_frames", 30)
        self._tracker = ByteTrackWrapper(
            max_lost_frames=max_lost_frames, fps=fps
        )

        # Initialise staff filter
        staff_config = config.get("staff_colour", None)
        self._staff_filter = StaffFilter(config=staff_config)

        self._frame_id: int = 0
        self._running: bool = False

    async def run(self) -> None:
        """Main pipeline loop. Reads frames, detects, tracks, and emits.

        On camera feed loss: logs interruption, polls for reconnect every 2s,
        preserves active track state.
        """
        self._running = True
        logger.info("DetectionPipeline [%s] started", self._camera_id)

        try:
            while self._running:
                try:
                    await self._process_frames()
                except (RuntimeError, OSError) as exc:
                    # Camera feed loss
                    logger.warning(
                        "DetectionPipeline [%s] feed lost at %s: %s",
                        self._camera_id,
                        datetime.now(timezone.utc).isoformat(),
                        exc,
                    )
                    # Poll for reconnect — preserve track state
                    await self._wait_for_reconnect()
        except asyncio.CancelledError:
            logger.info("DetectionPipeline [%s] cancelled", self._camera_id)
            raise
        finally:
            self._running = False
            logger.info("DetectionPipeline [%s] stopped", self._camera_id)

    async def _process_frames(self) -> None:
        """Process frames from the video source."""
        for frame in self._video_source.frames():
            if not self._running:
                break

            track_frame = self._process_single_frame(frame)

            if track_frame is not None:
                await self._track_queue.put(track_frame)

            # Yield to event loop to allow other coroutines to run
            await asyncio.sleep(0)

    def _process_single_frame(self, frame: np.ndarray) -> TrackFrame | None:
        """Run detection, tracking, and classification on a single frame.

        Args:
            frame: BGR numpy array.

        Returns:
            TrackFrame with detections, or None if no valid detections.
        """
        self._frame_id += 1
        timestamp = datetime.now(timezone.utc)

        frame_h, frame_w = frame.shape[:2]

        # Run YOLOv8n inference — person class only, confidence threshold
        results = self._model(
            frame,
            classes=[_PERSON_CLASS_ID],
            conf=self._confidence_threshold,
            device=self._device,
            verbose=False,
        )

        # Extract detections from YOLO results
        raw_detections: list[dict] = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                # Get pixel coordinates
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                x1_px, y1_px, x2_px, y2_px = xyxy

                # Filter by bbox height (pixel space)
                bbox_height = y2_px - y1_px
                if bbox_height < self._min_bbox_height_px:
                    continue

                # Normalise to [0.0, 1.0]
                x1 = float(x1_px / frame_w)
                y1 = float(y1_px / frame_h)
                x2 = float(x2_px / frame_w)
                y2 = float(y2_px / frame_h)

                # Clamp to [0, 1]
                x1 = max(0.0, min(1.0, x1))
                y1 = max(0.0, min(1.0, y1))
                x2 = max(0.0, min(1.0, x2))
                y2 = max(0.0, min(1.0, y2))

                raw_detections.append(
                    {
                        "bbox": (x1, y1, x2, y2),
                        "confidence": conf,
                        "class_id": _PERSON_CLASS_ID,
                    }
                )

        # Apply ByteTrack
        tracked = self._tracker.update(raw_detections)

        # Build TrackFrame with staff classification
        detections: list[TrackDetection] = []
        for det in tracked:
            bbox = det["bbox"]
            confidence = det["confidence"]

            # Clamp values to valid range for dataclass validation
            confidence = max(0.0, min(1.0, confidence))
            bbox = tuple(max(0.0, min(1.0, v)) for v in bbox)

            # Classify as visitor or staff
            role = self._staff_filter.classify(
                bbox=bbox,
                frame=frame,
                config=self._config.get("staff_colour"),
            )

            detections.append(
                TrackDetection(
                    track_id=det["track_id"],
                    bbox=bbox,
                    confidence=confidence,
                    role=role,
                )
            )

        track_frame = TrackFrame(
            camera_id=self._camera_id,
            frame_id=self._frame_id,
            timestamp=timestamp,
            detections=detections,
        )

        return track_frame

    async def _wait_for_reconnect(self) -> None:
        """Poll for video source reconnect every configured interval."""
        while self._running:
            logger.info(
                "DetectionPipeline [%s] polling for reconnect...",
                self._camera_id,
            )
            await asyncio.sleep(self._reconnect_interval)

            try:
                # Attempt to re-initialise the video source
                # The video source's frames() generator will restart on next call
                # to _process_frames if the source is back
                return
            except Exception as exc:
                logger.warning(
                    "DetectionPipeline [%s] reconnect failed: %s",
                    self._camera_id,
                    exc,
                )

    def stop(self) -> None:
        """Signal the pipeline to stop processing."""
        self._running = False
