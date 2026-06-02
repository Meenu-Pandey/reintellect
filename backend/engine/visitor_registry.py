"""
Visitor registry: assigns and manages stable visitor IDs.

Maps internal track_ids to business-level visitor_ids. Handles re-entry
detection and camera handoff merging.
"""

from __future__ import annotations

import uuid
from datetime import datetime


class VisitorRegistry:
    """Manages track_id → visitor_id mapping with re-entry handling.

    Rules:
    - New track_id → new UUID v4 visitor_id
    - Re-entry within 300s of exit → reuse original visitor_id
    - Re-entry at >= 300s → new visitor_id
    - Camera handoff merge if gap <= 10s
    """

    def __init__(self) -> None:
        # track_id → visitor_id
        self._track_to_visitor: dict[int, str] = {}
        # visitor_id → exit timestamp
        self._exit_times: dict[str, datetime] = {}
        # visitor_id → track_id (reverse lookup for re-entry)
        self._visitor_to_track: dict[str, int] = {}

    def get_or_assign(self, track_id: int, entry_time: datetime) -> str:
        """Get existing visitor_id for track or assign a new one.

        Args:
            track_id: ByteTrack-assigned track ID.
            entry_time: Timestamp of the detection.

        Returns:
            Stable visitor_id (UUID v4 string).
        """
        if track_id in self._track_to_visitor:
            return self._track_to_visitor[track_id]

        visitor_id = str(uuid.uuid4())
        self._track_to_visitor[track_id] = visitor_id
        self._visitor_to_track[visitor_id] = track_id
        return visitor_id

    def record_exit(self, visitor_id: str, exit_time: datetime) -> None:
        """Record that a visitor has exited the store.

        Args:
            visitor_id: The visitor's ID.
            exit_time: Timestamp of the exit event.
        """
        self._exit_times[visitor_id] = exit_time

    def handle_reentry(
        self, track_id: int, reentry_time: datetime
    ) -> tuple[str, float]:
        """Handle a re-entry detection.

        If the visitor exited less than 300s ago, reuse their visitor_id.
        Otherwise, assign a new visitor_id.

        Args:
            track_id: The new track_id for the re-entering person.
            reentry_time: Timestamp of re-entry.

        Returns:
            Tuple of (visitor_id, gap_seconds).
        """
        # Look for recently exited visitors — find the most recent exit
        best_visitor_id: str | None = None
        best_gap: float = float("inf")

        for vid, exit_time in self._exit_times.items():
            gap = (reentry_time - exit_time).total_seconds()
            if 0 <= gap < best_gap:
                best_gap = gap
                best_visitor_id = vid

        if best_visitor_id is not None and best_gap < 300.0:
            # Reuse original visitor_id
            self._track_to_visitor[track_id] = best_visitor_id
            self._visitor_to_track[best_visitor_id] = track_id
            # Remove from exit_times since they're back
            del self._exit_times[best_visitor_id]
            return best_visitor_id, best_gap
        else:
            # Assign new visitor_id
            visitor_id = str(uuid.uuid4())
            self._track_to_visitor[track_id] = visitor_id
            self._visitor_to_track[visitor_id] = track_id
            gap = best_gap if best_gap != float("inf") else 0.0
            return visitor_id, gap

    def merge_camera_handoff(
        self, old_track_id: int, new_track_id: int, gap_seconds: float
    ) -> None:
        """Merge two track segments from a camera handoff.

        If the gap between the old track disappearing and the new track
        appearing is <= 10s, they are considered the same visitor.

        Args:
            old_track_id: The track_id that was lost.
            new_track_id: The track_id that appeared.
            gap_seconds: Time gap between last detection of old and first of new.
        """
        if gap_seconds > 10.0:
            return

        if old_track_id not in self._track_to_visitor:
            return

        # Merge: assign the old visitor_id to the new track
        visitor_id = self._track_to_visitor[old_track_id]
        self._track_to_visitor[new_track_id] = visitor_id
        self._visitor_to_track[visitor_id] = new_track_id

    def get_visitor_id(self, track_id: int) -> str | None:
        """Look up visitor_id for a track_id, or None if not registered."""
        return self._track_to_visitor.get(track_id)
