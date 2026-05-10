---
plan: 4.1
status: complete
---

# P4.1 — 事件数据模型 + 存储

## 完成内容

- 创建 `data/event.py` — Event dataclass（title, datetime_str, description, category, priority, calendar_id, deadline_str, status, id）
- 创建 `data/schedule_store.py` — ScheduleStore 基于 JsonStore 的 CRUD 封装（add, get_all, get_by_id, update, delete）
- 创建 `data/__init__.py`

## 关键文件

- `data/event.py` — Event 数据模型
- `data/schedule_store.py` — 事件存储 CRUD
