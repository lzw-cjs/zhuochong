---
plan: 4.2
status: complete
---

# P4.2 — 多日历支持

## 完成内容

- 创建 `data/calendar_model.py` — Calendar dataclass（id, name, color）
- 创建 `data/calendar_store.py` — CalendarStore 基于 JsonStore 的 CRUD 封装，支持默认日历
- 支持按 calendar_id 过滤事件

## 关键文件

- `data/calendar_model.py` — 日历数据模型
- `data/calendar_store.py` — 日历存储 CRUD
