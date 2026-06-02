"""
Unit tests for VisitorRegistry.

Tests:
- New visitor assignment
- Re-entry at 299s (same ID)
- Re-entry at 300s (new ID)
- Camera handoff within 10s
"""

from datetime import datetime, timedelta, timezone

from engine.visitor_registry import VisitorRegistry


BASE_TIME = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_new_visitor_assignment():
    """New track_id gets a new UUID visitor_id."""
    registry = VisitorRegistry()

    vid = registry.get_or_assign(1, BASE_TIME)

    assert vid is not None
    assert len(vid) == 36  # UUID v4 format
    # Same track_id returns same visitor_id
    assert registry.get_or_assign(1, BASE_TIME) == vid


def test_reentry_at_299s_same_id():
    """Re-entry within 300s reuses the original visitor_id."""
    registry = VisitorRegistry()

    vid1 = registry.get_or_assign(1, BASE_TIME)
    registry.record_exit(vid1, BASE_TIME)

    reentry_time = BASE_TIME + timedelta(seconds=299)
    vid2, gap = registry.handle_reentry(2, reentry_time)

    assert vid2 == vid1
    assert gap == 299.0


def test_reentry_at_300s_new_id():
    """Re-entry at >= 300s assigns a new visitor_id."""
    registry = VisitorRegistry()

    vid1 = registry.get_or_assign(1, BASE_TIME)
    registry.record_exit(vid1, BASE_TIME)

    reentry_time = BASE_TIME + timedelta(seconds=300)
    vid2, gap = registry.handle_reentry(2, reentry_time)

    assert vid2 != vid1
    assert gap == 300.0


def test_camera_handoff_within_10s():
    """Camera handoff within 10s merges to same visitor_id."""
    registry = VisitorRegistry()

    vid1 = registry.get_or_assign(1, BASE_TIME)

    # Handoff: old track 1 lost, new track 2 appears within 10s
    registry.merge_camera_handoff(old_track_id=1, new_track_id=2, gap_seconds=8.0)

    # New track should have the same visitor_id
    vid2 = registry.get_visitor_id(2)
    assert vid2 == vid1


def test_camera_handoff_beyond_10s_no_merge():
    """Camera handoff beyond 10s does NOT merge."""
    registry = VisitorRegistry()

    vid1 = registry.get_or_assign(1, BASE_TIME)

    registry.merge_camera_handoff(old_track_id=1, new_track_id=2, gap_seconds=11.0)

    # New track should NOT have the old visitor_id
    vid2 = registry.get_visitor_id(2)
    assert vid2 is None
