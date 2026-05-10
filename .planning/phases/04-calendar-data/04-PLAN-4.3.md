---
wave: 1
depends_on:
  - P4.1
  - P4.2
files_modified:
  - pet/schedule_panel.py
  - pet/__init__.py
  - main.py
autonomous: true
---

# P4.3 — 日程面板 UI

## 目标

实现日程面板：左侧日历列表、右侧事件列表、新建/编辑/删除事件对话框。

**覆盖需求：** SCH-01, SCH-02, SCH-03

---

## 任务

### 任务 1：实现 SchedulePanel

创建 `pet/schedule_panel.py`，包含：

- `SchedulePanel`: 主面板窗口（480x560）
  - 左侧：日历列表（QListWidget），可勾选显示/隐藏
  - 右侧：事件列表（QListWidget），按时间排序
  - 底部：新建事件按钮
  - 双击事件打开编辑对话框

- `EventDialog`: 新建/编辑事件对话框
  - 标题输入（QLineEdit）
  - 日期时间选择（QDateTimeEdit）
  - 描述输入（QTextEdit）
  - 分类选择（QComboBox: 工作/学习/生活/其他）
  - 优先级选择（QComboBox: 低/中/高）
  - 日历选择（QComboBox）
  - 确定/取消按钮

### 任务 2：集成到 main.py

连接右键菜单"日程"到面板显示。

**验收标准：**
- 面板显示事件列表
- 可以新建事件
- 可以编辑事件（双击）
- 可以删除事件
- 事件按时间排序
- 关闭面板不退出应用
