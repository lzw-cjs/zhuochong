"""提醒引擎：事件前提醒（区别于超时检测器）"""
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer, Signal, QObject

from data.event import Event
from data.schedule_store import ScheduleStore


class ReminderEngine(QObject):
    """主动提醒引擎。每 60 秒轮询一次，事件进入提醒窗口时发射信号。"""

    reminder_fired = Signal(Event)

    def __init__(self, store: ScheduleStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._fired: set[str] = set()
        self._suppressed: bool = False

        self._timer = QTimer()
        self._timer.timeout.connect(self._check)
        self._timer.start(60000)

    def suppress(self, suppress: bool) -> None:
        self._suppressed = suppress

    def clear_fired(self, event_id: str | None = None) -> None:
        if event_id:
            self._fired.discard(event_id)
        else:
            self._fired.clear()

    def _check(self) -> None:
        if self._suppressed:
            return
        now = datetime.now()
        for ev in self._store.get_all():
            if ev.status != "pending" or not ev.datetime_str:
                continue
            if ev.id in self._fired:
                continue
            try:
                event_time = datetime.fromisoformat(ev.datetime_str)
            except ValueError:
                continue
            reminder_time = event_time - timedelta(minutes=ev.reminder_minutes)
            if now >= reminder_time:
                self._fired.add(ev.id)
                self.reminder_fired.emit(ev)
