"""临时提醒管理器 — 自然语言创建的定时提醒"""
import uuid
from PySide6.QtCore import QObject, Signal, QTimer


class TempReminderManager(QObject):
    """管理临时提醒，基于 QTimer 实现延迟触发。"""

    reminder_fired = Signal(str)  # 提醒文本

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timers: dict[str, QTimer] = {}

    def add_reminder(self, text: str, delay_minutes: int) -> str:
        """创建临时提醒，返回确认消息。

        Args:
            text: 提醒内容
            delay_minutes: 多少分钟后触发

        Returns:
            确认消息字符串
        """
        rid = uuid.uuid4().hex[:8]
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._on_fired(rid, text))
        timer.start(int(delay_minutes * 60 * 1000))
        self._timers[rid] = timer
        return f"好的！{delay_minutes}分钟后提醒你：{text}"

    def _on_fired(self, rid: str, text: str):
        """提醒触发时清理并发射信号。"""
        self._timers.pop(rid, None)
        self.reminder_fired.emit(text)

    def cancel_all(self) -> None:
        """取消所有临时提醒。"""
        for t in self._timers.values():
            t.stop()
        self._timers.clear()
