---
plan: 4.4
status: complete
---

# P4.4 — 导入导出

## 完成内容

- ScheduleStore 添加 `export_json()` 方法 — 导出所有事件到 JSON 文件
- ScheduleStore 添加 `import_json()` 方法 — 从 JSON 文件导入事件（去重）
- SchedulePanel 添加导入导出按钮和文件对话框
- 支持 Markdown/纯文本/JSON 多格式导入 + 自动事件提取
- 支持粘贴导入功能

## 关键文件

- `data/schedule_store.py` — export_json / import_json 方法
- `pet/schedule_panel.py` — 导入导出 UI 集成
