"""Tests for EventDialog reminder timing QComboBox.

Verifies REM-02: configurable reminder timing (5/15/30/60 minutes).
"""
import sys
import pytest
from unittest.mock import MagicMock

# PySide6 requires QApplication for any widget construction
from PySide6.QtWidgets import QApplication

# Ensure a QApplication exists (required before any QWidget is created)
_app = QApplication.instance() or QApplication(sys.argv)

from data.event import Event
from data.calendar_model import Calendar
from pet.schedule_panel import EventDialog


def _make_calendars():
    """Return a minimal list of calendars for EventDialog."""
    return [Calendar(name="Default", color="#4A90D9", id="default")]


def _make_event(**kwargs):
    """Create an Event with sensible defaults, overriding via kwargs."""
    defaults = dict(
        title="Test",
        datetime_str="2026-05-10T10:00:00",
        description="",
        category="其他",
        priority="medium",
        calendar_id="default",
        reminder_minutes=15,
        deadline_str="",
        completed=False,
        completed_at="",
        status="pending",
        id="test123",
    )
    defaults.update(kwargs)
    return Event(**defaults)


class TestReminderDefault:
    """New event dialog defaults to 15 minutes."""

    def test_default_reminder_is_15(self):
        dlg = EventDialog(None, _make_calendars())
        ev = dlg.get_event()
        assert ev.reminder_minutes == 15


class TestReminderPreservation:
    """Existing event with custom reminder_minutes preserves it."""

    def test_existing_60_preserved(self):
        event = _make_event(reminder_minutes=60)
        dlg = EventDialog(event, _make_calendars())
        ev = dlg.get_event()
        assert ev.reminder_minutes == 60

    def test_existing_5_preserved(self):
        event = _make_event(reminder_minutes=5)
        dlg = EventDialog(event, _make_calendars())
        ev = dlg.get_event()
        assert ev.reminder_minutes == 5


class TestReminderSelection:
    """Each combo box option maps to the correct minute value."""

    @pytest.mark.parametrize(
        "index,expected_minutes",
        [(0, 5), (1, 15), (2, 30), (3, 60)],
    )
    def test_combo_index_maps_to_minutes(self, index, expected_minutes):
        dlg = EventDialog(None, _make_calendars())
        dlg._reminder.setCurrentIndex(index)
        ev = dlg.get_event()
        assert ev.reminder_minutes == expected_minutes


class TestReminderComboStructure:
    """QComboBox has exactly 4 items with correct labels and data."""

    def test_combo_item_count(self):
        dlg = EventDialog(None, _make_calendars())
        assert dlg._reminder.count() == 4

    def test_combo_labels(self):
        dlg = EventDialog(None, _make_calendars())
        expected = ["5 分钟", "15 分钟", "30 分钟", "1 小时"]
        for i, label in enumerate(expected):
            assert dlg._reminder.itemText(i) == label

    def test_combo_data(self):
        dlg = EventDialog(None, _make_calendars())
        expected = [5, 15, 30, 60]
        for i, minutes in enumerate(expected):
            assert dlg._reminder.itemData(i) == minutes
