"""超时检测器：检测超过截止时间的事件"""
from datetime import datetime
from PySide6.QtCore import QTimer, Signal, QObject

from data.event import Event
from data.schedule_store import ScheduleStore


class ReminderEngine(QObject):
    """定时检测超时事件。

    每 30 秒检查一次，发现超时事件发射 overdue 信号。
    """

    overdue = Signal(Event)  # 超时事件信号
    completed_early = Signal(Event)  # 提前完成信号

    def __init__(self, store: ScheduleStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._notified: set[str] = set()  # 已通知的事件 ID

        self._timer = QTimer()
        self._timer.timeout.connect(self._check)
        self._timer.start(30000)  # 30 秒检查一次

    def _check(self):
        """检查超时事件。"""
        now = datetime.now()
        for ev in self._store.get_all():
            if ev.status != "pending" or not ev.deadline_str:
                continue
            if ev.id in self._notified:
                continue
            try:
                deadline = datetime.fromisoformat(ev.deadline_str)
            except ValueError:
                continue
            if now > deadline:
                # 标记为超时
                ev.status = "overdue"
                self._store.update(ev)
                self._notified.add(ev.id)
                self.overdue.emit(ev)

    def mark_completed(self, event_id: str) -> bool:
        """标记事件完成。如果在截止时间前完成，发射 completed_early 信号。"""
        ev = self._store.get_by_id(event_id)
        if not ev or ev.status != "pending":
            return False
        now = datetime.now()
        ev.completed = True
        ev.completed_at = now.isoformat()
        if ev.deadline_str:
            try:
                deadline = datetime.fromisoformat(ev.deadline_str)
                if now < deadline:
                    ev.status = "completed"
                    self._store.update(ev)
                    self.completed_early.emit(ev)
                    return True
            except ValueError:
                pass
        ev.status = "completed"
        self._store.update(ev)
        return True

    def extend_deadline(self, event_id: str, hours: int = 1) -> bool:
        """延长截止时间。"""
        ev = self._store.get_by_id(event_id)
        if not ev:
            return False
        if ev.deadline_str:
            try:
                deadline = datetime.fromisoformat(ev.deadline_str)
                from datetime import timedelta
                new_deadline = deadline + timedelta(hours=hours)
                ev.deadline_str = new_deadline.isoformat()
                ev.status = "pending"
                self._store.update(ev)
                self._notified.discard(ev.id)
                return True
            except ValueError:
                pass
        return False

    def cancel_event(self, event_id: str) -> bool:
        """取消事件（标记为已完成，不再提醒）。"""
        ev = self._store.get_by_id(event_id)
        if not ev:
            return False
        ev.status = "completed"
        ev.completed = True
        ev.completed_at = datetime.now().isoformat()
        self._store.update(ev)
        self._notified.discard(ev.id)
        return True

    def daily_check(self):
        """每日全量扫描：标记所有过期事件。"""
        now = datetime.now()
        for ev in self._store.get_all():
            if ev.status != "pending":
                continue
            if ev.id in self._notified:
                continue
            # 有截止时间：以截止时间为准
            if ev.deadline_str:
                try:
                    deadline = datetime.fromisoformat(ev.deadline_str)
                    if now > deadline:
                        ev.status = "overdue"
                        self._store.update(ev)
                        self._notified.add(ev.id)
                        self.overdue.emit(ev)
                except ValueError:
                    pass
            # 无截止时间：以事件时间为准
            elif ev.datetime_str:
                try:
                    event_time = datetime.fromisoformat(ev.datetime_str)
                    if now > event_time:
                        ev.status = "overdue"
                        self._store.update(ev)
                        self._notified.add(ev.id)
                        self.overdue.emit(ev)
                except ValueError:
                    pass
