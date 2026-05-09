"""Shared test fixtures for the Smart Desktop Pet test suite."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from data.event import Event
from data.schedule_store import ScheduleStore


_SENTINEL = object()


@pytest.fixture
def make_event():
    """Factory for creating Event objects with sensible defaults."""
    def _make(
        title: str = "Test Event",
        datetime_str: str = _SENTINEL,
        reminder_minutes: int = 15,
        status: str = "pending",
        id: str = "test-evt-001",
        deadline_str: str = "",
        completed: bool = False,
        **kwargs,
    ) -> Event:
        if datetime_str is _SENTINEL:
            datetime_str = (datetime.now() + timedelta(minutes=10)).isoformat()
        return Event(
            title=title,
            datetime_str=datetime_str,
            reminder_minutes=reminder_minutes,
            status=status,
            id=id,
            deadline_str=deadline_str,
            completed=completed,
            **kwargs,
        )
    return _make


@pytest.fixture
def mock_store():
    """Returns a mock ScheduleStore with configurable get_all()."""
    store = MagicMock(spec=ScheduleStore)
    store.get_all.return_value = []
    return store
