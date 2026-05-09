"""Tests for ReminderEngine — event pre-reminder with dedup and suppression."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from pet.reminder_engine import ReminderEngine
from data.event import Event


class TestReminderFires:
    """Test that reminders fire within the correct time window."""

    def test_reminder_fires_within_window(self, mock_store, make_event):
        """Event 10 min away with 15 min reminder -> signal fires."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=10)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()

        assert len(fired) == 1
        assert fired[0].id == evt.id

    def test_reminder_does_not_fire_outside_window(self, mock_store, make_event):
        """Event 30 min away with 15 min reminder -> no signal."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=30)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()

        assert len(fired) == 0


class TestDeduplication:
    """Test that the same event does not fire twice."""

    def test_deduplication(self, mock_store, make_event):
        """Fire once, check again -> no second fire."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()
        engine._check()

        assert len(fired) == 1


class TestSuppression:
    """Test that suppression blocks and restores reminders."""

    def test_suppress_blocks_reminders(self, mock_store, make_event):
        """suppress(True) prevents firing."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine.suppress(True)
        engine._check()

        assert len(fired) == 0

    def test_unsuppress_restores_reminders(self, mock_store, make_event):
        """suppress(False) allows firing."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine.suppress(True)
        engine._check()
        assert len(fired) == 0

        engine.suppress(False)
        engine._check()
        assert len(fired) == 1


class TestClearFired:
    """Test that clear_fired allows re-firing."""

    def test_clear_fired_single(self, mock_store, make_event):
        """clear_fired(event_id) allows re-fire for that event."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()
        assert len(fired) == 1

        engine.clear_fired(evt.id)
        engine._check()
        assert len(fired) == 2

    def test_clear_fired_all(self, mock_store, make_event):
        """clear_fired() allows re-fire for all events."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()
        assert len(fired) == 1

        engine.clear_fired()
        engine._check()
        assert len(fired) == 2


class TestEdgeCases:
    """Test edge cases: completed events, empty/invalid datetime."""

    def test_skips_completed_events(self, mock_store, make_event):
        """status='completed' -> skipped even if within window."""
        evt = make_event(
            datetime_str=(datetime.now() + timedelta(minutes=5)).isoformat(),
            reminder_minutes=15,
            status="completed",
        )
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()

        assert len(fired) == 0

    def test_skips_empty_datetime(self, mock_store, make_event):
        """datetime_str='' -> skipped, no crash."""
        evt = make_event(datetime_str="", reminder_minutes=15)
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()

        assert len(fired) == 0

    def test_skips_invalid_datetime(self, mock_store, make_event):
        """datetime_str='not-a-date' -> skipped, no crash."""
        evt = make_event(datetime_str="not-a-date", reminder_minutes=15)
        mock_store.get_all.return_value = [evt]

        engine = ReminderEngine(mock_store)
        fired = []
        engine.reminder_fired.connect(lambda e: fired.append(e))

        engine._check()

        assert len(fired) == 0
