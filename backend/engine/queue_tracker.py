"""
Queue tracker: monitors billing queue membership and abandonment.

Tracks visitors joining the checkout queue, their wait time,
and detects abandonment when no POS transaction follows within 120s.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from engine.models import Event


class QueueTracker:
    """Tracks billing queue state: joins, depth, and abandonment.

    Attributes:
        _queue_members: visitor_id → join_time for currently queued visitors.
        _depth: Current number of visitors in the queue.
    """

    # Abandonment window: no POS transaction within this many seconds = abandon
    ABANDON_WINDOW_SECONDS: float = 120.0

    def __init__(self, store_id: str, camera_id: str) -> None:
        """Initialise the queue tracker.

        Args:
            store_id: Store identifier for emitted events.
            camera_id: Camera identifier for emitted events.
        """
        self._store_id = store_id
        self._camera_id = camera_id
        self._queue_members: dict[str, datetime] = {}
        self._depth: int = 0

    def join(self, visitor_id: str, timestamp: datetime) -> Event:
        """Record a visitor joining the billing queue.

        Args:
            visitor_id: The visitor's stable ID.
            timestamp: When they joined the queue.

        Returns:
            BILLING_QUEUE_JOIN event with queue_position.
        """
        self._depth += 1
        self._queue_members[visitor_id] = timestamp

        return Event(
            event_id=str(uuid.uuid4()),
            event_type="BILLING_QUEUE_JOIN",
            store_id=self._store_id,
            visitor_id=visitor_id,
            timestamp=timestamp,
            camera_id=self._camera_id,
            attributes={"queue_position": self._depth},
        )

    def check_abandon(
        self,
        visitor_id: str,
        exit_time: datetime,
        pos_transactions: list[dict],
    ) -> Event | None:
        """Check if a visitor abandoned the queue.

        Emits BILLING_QUEUE_ABANDON if no POS transaction is linked to this
        visitor within 120s of their queue join time.

        Args:
            visitor_id: The visitor who left the queue zone.
            exit_time: When they left.
            pos_transactions: List of POS transaction dicts with at least
                'visitor_id' and 'timestamp' fields.

        Returns:
            BILLING_QUEUE_ABANDON event if abandoned, None otherwise.
        """
        if visitor_id not in self._queue_members:
            return None

        join_time = self._queue_members[visitor_id]

        # Check if there's a POS transaction for this visitor within the window
        for txn in pos_transactions:
            if txn.get("visitor_id") != visitor_id:
                continue
            txn_time = txn.get("timestamp")
            if txn_time is None:
                continue
            gap = (txn_time - join_time).total_seconds()
            if 0 <= gap <= self.ABANDON_WINDOW_SECONDS:
                # Transaction found — not abandoned
                del self._queue_members[visitor_id]
                self._depth = max(0, self._depth - 1)
                return None

        # No matching transaction — abandoned
        wait_seconds = (exit_time - join_time).total_seconds()
        del self._queue_members[visitor_id]
        self._depth = max(0, self._depth - 1)

        return Event(
            event_id=str(uuid.uuid4()),
            event_type="BILLING_QUEUE_ABANDON",
            store_id=self._store_id,
            visitor_id=visitor_id,
            timestamp=exit_time,
            camera_id=self._camera_id,
            attributes={"wait_seconds": wait_seconds},
        )

    def get_depth(self) -> int:
        """Return current live queue depth."""
        return self._depth

    def remove(self, visitor_id: str) -> None:
        """Remove a visitor from the queue (e.g. after successful checkout).

        Args:
            visitor_id: The visitor to remove.
        """
        if visitor_id in self._queue_members:
            del self._queue_members[visitor_id]
            self._depth = max(0, self._depth - 1)
