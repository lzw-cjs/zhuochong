---
wave: 0
depends_on: []
files_modified:
  - data/event.py
  - data/schedule_store.py
  - data/__init__.py
autonomous: true
---

# P4.1 — 事件数据模型 + 存储

## 目标

实现 Event dataclass 和 ScheduleStore（基于 JsonStore 的 CRUD 封装）。

**覆盖需求：** SCH-01, SCH-03

---

## 任务

### 任务 1：实现 Event 数据模型

创建 `data/event.py`：

```python
"""日程事件数据模型"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


@dataclass
class Event:
    """日程事件。"""
    title: str
    datetime_str: str  # ISO 8601 格式
    description: str = ""
    category: str = "其他"  # 工作/学习/生活/其他
    priority: str = "medium"  # low/medium/high
    calendar_id: str = "default"
    reminder_minutes: int = 15
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
```

### 任务 2：实现 ScheduleStore

创建 `data/schedule_store.py`：

```python
"""日程事件存储"""
from data.store import JsonStore
from data.event import Event


class ScheduleStore:
    """事件 CRUD 操作。"""

    def __init__(self):
        self._store = JsonStore("events.json")

    def _load_events(self) -> list[dict]:
        data = self._store.load(default={"events": []})
        return data.get("events", [])

    def _save_events(self, events: list[dict]) -> None:
        self._store.save({"events": events})

    def add(self, event: Event) -> None:
        events = self._load_events()
        events.append(event.to_dict())
        self._save_events(events)

    def get_all(self) -> list[Event]:
        return [Event.from_dict(d) for d in self._load_events()]

    def get_by_id(self, event_id: str) -> Event | None:
        for e in self.get_all():
            if e.id == event_id:
                return e
        return None

    def update(self, event: Event) -> bool:
        events = self._load_events()
        for i, d in enumerate(events):
            if d.get("id") == event.id:
                events[i] = event.to_dict()
                self._save_events(events)
                return True
        return False

    def delete(self, event_id: str) -> bool:
        events = self._load_events()
        before = len(events)
        events = [d for d in events if d.get("id") != event_id]
        if len(events) < before:
            self._save_events(events)
            return True
        return False
```

### 任务 3：更新 data/__init__.py

添加 `Event` 和 `ScheduleStore` 导出。

**验收标准：**
- `data/event.py` 包含 `class Event` 和所有字段
- `data/schedule_store.py` 包含 CRUD 方法
- `data/__init__.py` 导出新类
