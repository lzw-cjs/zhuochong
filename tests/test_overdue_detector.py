"""Tests for renamed overdue detector module."""
import pytest


def test_import_from_new_path():
    """Importing from pet.overdue_detector succeeds."""
    from pet.overdue_detector import ReminderEngine
    assert ReminderEngine is not None


def test_has_overdue_signal():
    """ReminderEngine from overdue_detector has overdue signal."""
    from pet.overdue_detector import ReminderEngine
    assert hasattr(ReminderEngine, 'overdue')


def test_has_completed_early_signal():
    """ReminderEngine from overdue_detector has completed_early signal."""
    from pet.overdue_detector import ReminderEngine
    assert hasattr(ReminderEngine, 'completed_early')
