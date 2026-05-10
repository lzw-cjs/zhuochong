# Phase 4 Context — 日程数据层

## 范围

Phase 4 实现日程事件的完整 CRUD、多日历支持、日程面板 UI、JSON 导入导出。

**需求：** SCH-01, SCH-02, SCH-03, SCH-04

## 设计决策

### D-01: Event 数据模型
- 字段：id, title, datetime, description, category, priority, calendar_id, reminder_minutes
- id 使用 UUID 字符串
- datetime 使用 ISO 8601 格式字符串
- priority: low/medium/high
- category: 工作/学习/生活/其他

### D-02: Calendar 数据模型
- 字段：id, name, color
- 默认日历："默认"（棕色）
- 预设颜色：棕/蓝/绿/红/紫

### D-03: 存储结构
- events.json: 事件列表
- calendars.json: 日历列表
- 使用 JsonStore 原子写入

### D-04: 日程面板
- 左侧：日历列表（可选中/取消）
- 右侧：事件列表（按时间排序）
- 底部：新建事件按钮
- 双击事件打开编辑对话框
