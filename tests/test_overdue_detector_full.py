"""OverdueDetector (ReminderEngine) 完整单元测试"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from data.event import Event


def make_event(**kwargs):
    defaults = {
        "id": "test-1",
        "title": "测试事件",
        "datetime_str": datetime.now().isoformat(),
        "status": "pending",
    }
    defaults.update(kwargs)
    return Event(**defaults)


class TestReminderEngineOverdue:
    """超时检测测试"""

    @patch("pet.overdue_detector.QTimer")
    def test_init(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        engine = ReminderEngine(store)

        assert engine._store is store
        assert len(engine._notified) == 0

    @patch("pet.overdue_detector.QTimer")
    def test_check_detects_overdue(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(
                id="overdue-1",
                deadline_str=(datetime.now() - timedelta(hours=1)).isoformat(),
            )
        ]

        engine = ReminderEngine(store)
        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine._check()

        assert len(overdue_events) == 1
        assert overdue_events[0].id == "overdue-1"
        assert "overdue-1" in engine._notified

    @patch("pet.overdue_detector.QTimer")
    def test_check_skips_pending_within_deadline(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(
                id="not-overdue",
                deadline_str=(datetime.now() + timedelta(hours=1)).isoformat(),
            )
        ]

        engine = ReminderEngine(store)
        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine._check()

        assert len(overdue_events) == 0

    @patch("pet.overdue_detector.QTimer")
    def test_check_skips_already_notified(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(
                id="already-notified",
                deadline_str=(datetime.now() - timedelta(hours=1)).isoformat(),
            )
        ]

        engine = ReminderEngine(store)
        engine._notified.add("already-notified")

        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine._check()

        assert len(overdue_events) == 0

    @patch("pet.overdue_detector.QTimer")
    def test_check_skips_non_pending(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(
                id="completed-event",
                status="completed",
                deadline_str=(datetime.now() - timedelta(hours=1)).isoformat(),
            )
        ]

        engine = ReminderEngine(store)
        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine._check()

        assert len(overdue_events) == 0

    @patch("pet.overdue_detector.QTimer")
    def test_check_skips_no_deadline(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(id="no-deadline", deadline_str="")
        ]

        engine = ReminderEngine(store)
        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine._check()

        assert len(overdue_events) == 0

    @patch("pet.overdue_detector.QTimer")
    def test_mark_completed(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        event = make_event(
            id="evt-1",
            deadline_str=(datetime.now() + timedelta(hours=1)).isoformat(),
        )
        store = MagicMock()
        store.get_by_id.return_value = event

        engine = ReminderEngine(store)
        completed_signals = []
        engine.completed_early.connect(lambda e: completed_signals.append(e))

        result = engine.mark_completed("evt-1")

        assert result is True
        assert event.completed is True
        assert event.status == "completed"
        assert len(completed_signals) == 1

    @patch("pet.overdue_detector.QTimer")
    def test_mark_completed_past_deadline(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        event = make_event(
            id="evt-1",
            deadline_str=(datetime.now() - timedelta(hours=1)).isoformat(),
        )
        store = MagicMock()
        store.get_by_id.return_value = event

        engine = ReminderEngine(store)
        completed_signals = []
        engine.completed_early.connect(lambda e: completed_signals.append(e))

        result = engine.mark_completed("evt-1")

        assert result is True
        assert len(completed_signals) == 0  # 不是提前完成

    @patch("pet.overdue_detector.QTimer")
    def test_mark_completed_nonexistent(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_by_id.return_value = None

        engine = ReminderEngine(store)
        result = engine.mark_completed("nonexistent")

        assert result is False

    @patch("pet.overdue_detector.QTimer")
    def test_extend_deadline(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        event = make_event(
            id="evt-1",
            deadline_str=datetime.now().isoformat(),
        )
        store = MagicMock()
        store.get_by_id.return_value = event

        engine = ReminderEngine(store)
        engine._notified.add("evt-1")

        result = engine.extend_deadline("evt-1", hours=2)

        assert result is True
        assert "evt-1" not in engine._notified
        assert event.status == "pending"

    @patch("pet.overdue_detector.QTimer")
    def test_extend_deadline_nonexistent(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_by_id.return_value = None

        engine = ReminderEngine(store)
        result = engine.extend_deadline("nonexistent")

        assert result is False

    @patch("pet.overdue_detector.QTimer")
    def test_cancel_event(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        event = make_event(id="evt-1")
        store = MagicMock()
        store.get_by_id.return_value = event

        engine = ReminderEngine(store)
        engine._notified.add("evt-1")

        result = engine.cancel_event("evt-1")

        assert result is True
        assert event.status == "completed"
        assert event.completed is True
        assert "evt-1" not in engine._notified

    @patch("pet.overdue_detector.QTimer")
    def test_cancel_event_nonexistent(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_by_id.return_value = None

        engine = ReminderEngine(store)
        result = engine.cancel_event("nonexistent")

        assert result is False

    @patch("pet.overdue_detector.QTimer")
    def test_daily_check(self, mock_timer_cls):
        from pet.overdue_detector import ReminderEngine

        store = MagicMock()
        store.get_all.return_value = [
            make_event(
                id="overdue-1",
                deadline_str=(datetime.now() - timedelta(hours=1)).isoformat(),
            ),
            make_event(
                id="not-overdue",
                deadline_str=(datetime.now() + timedelta(hours=1)).isoformat(),
            ),
        ]

        engine = ReminderEngine(store)
        overdue_events = []
        engine.overdue.connect(lambda e: overdue_events.append(e))

        engine.daily_check()

        assert len(overdue_events) == 1
        assert overdue_events[0].id == "overdue-1"
