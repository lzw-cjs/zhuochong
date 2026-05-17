"""主动对话管理器 — 空闲时主动聊天 + 日程提醒"""
import random
import time
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer


class ProactiveChatManager(QObject):
    """空闲检测 + 即将开始的日程主动提醒。"""

    trigger_chat = Signal(str)  # 主动消息文本

    def __init__(self, schedule_store, parent=None):
        super().__init__(parent)
        self._store = schedule_store
        self._last_interaction = time.time()
        self._notified_events: set[str] = set()  # 已提醒的事件 ID，避免重复

        # 每 30 分钟检查一次是否该主动说话
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_proactive)
        self._check_timer.start(30 * 60 * 1000)

        # 日程提醒（提前 10 分钟）
        self._event_timer = QTimer()
        self._event_timer.timeout.connect(self._check_upcoming_events)
        self._event_timer.start(60 * 1000)  # 每分钟检查

    def on_user_interaction(self) -> None:
        """记录用户交互时间。"""
        self._last_interaction = time.time()

    def _check_proactive(self) -> None:
        """空闲时主动聊天。"""
        idle_minutes = (time.time() - self._last_interaction) / 60
        if idle_minutes > 30:
            messages = [
                "主人好久没理我了，你在忙吗？(´・ω・`)",
                "主人~休息一下吧！",
                "你在做什么呀？我想你了~",
                "主人，要不要和我聊聊天？",
            ]
            self.trigger_chat.emit(random.choice(messages))

    def _check_upcoming_events(self) -> None:
        """即将开始的日程提醒。"""
        now = datetime.now()
        for event in self._store.get_all():
            if event.completed:
                continue
            if event.id in self._notified_events:
                continue
            try:
                event_time = datetime.fromisoformat(event.datetime_str)
                diff = (event_time - now).total_seconds()
                if 0 < diff <= 600:  # 10 分钟内
                    minutes_left = int(diff // 60)
                    self.trigger_chat.emit(
                        f"主人，{event.title} 快要开始了哦！还有{minutes_left}分钟~"
                    )
                    self._notified_events.add(event.id)
            except ValueError:
                pass
