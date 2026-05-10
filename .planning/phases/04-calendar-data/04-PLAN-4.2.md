---
wave: 0
depends_on: []
files_modified:
  - data/calendar.py
  - data/calendar_store.py
  - data/__init__.py
autonomous: true
---

# P4.2 — 多日历支持

## 目标

实现 Calendar dataclass 和 CalendarStore，支持多个日历（颜色区分）。

**覆盖需求：** SCH-02

---

## 任务

### 任务 1：实现 Calendar 数据模型

创建 `data/calendar_model.py`：

```python
"""日历数据模型"""
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class Calendar:
    """日历。"""
    name: str
    color: str = "#8B5A2B"  # 默认棕色
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Calendar":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# 预设颜色
CALENDAR_COLORS = {
    "棕色": "#8B5A2B",
    "蓝色": "#4A90D9",
    "绿色": "#5BA55B",
    "红色": "#D94A4A",
    "紫色": "#8B5AD9",
}
```

### 任务 2：实现 CalendarStore

创建 `data/calendar_store.py`：

```python
"""日历存储"""
from data.store import JsonStore
from data.calendar_model import Calendar


DEFAULT_CALENDAR = Calendar(id="default", name="默认", color="#8B5A2B")


class CalendarStore:
    """日历 CRUD 操作。"""

    def __init__(self):
        self._store = JsonStore("calendars.json")

    def _load(self) -> list[dict]:
        data = self._store.load(default={"calendars": [DEFAULT_CALENDAR.to_dict()]})
        cals = data.get("calendars", [])
        if not any(c.get("id") == "default" for c in cals):
            cals.insert(0, DEFAULT_CALENDAR.to_dict())
        return cals

    def _save(self, calendars: list[dict]) -> None:
        self._store.save({"calendars": calendars})

    def get_all(self) -> list[Calendar]:
        return [Calendar.from_dict(d) for d in self._load()]

    def add(self, cal: Calendar) -> None:
        cals = self._load()
        cals.append(cal.to_dict())
        self._save(cals)

    def delete(self, cal_id: str) -> bool:
        if cal_id == "default":
            return False  # 不能删除默认日历
        cals = self._load()
        before = len(cals)
        cals = [d for d in cals if d.get("id") != cal_id]
        if len(cals) < before:
            self._save(cals)
            return True
        return False
```

### 任务 3：更新 data/__init__.py

添加导出。

**验收标准：**
- Calendar 包含 id, name, color 字段
- CalendarStore 包含默认日历
- 不能删除 id="default" 的日历
