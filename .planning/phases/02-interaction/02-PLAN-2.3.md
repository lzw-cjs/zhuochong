---
wave: 1
depends_on:
  - P2.1
files_modified:
  - pet/window.py
  - main.py
autonomous: true
---

# P2.3 — Context Menu

## 目标

实现右键上下文菜单：在宠物窗口上右键弹出菜单，包含 Schedule、Chat、Settings、Exit 四个选项。Schedule/Chat/Settings 发射信号供 Phase 3+ 使用，Exit 直接退出应用。

**覆盖需求：** INT-01

---

## 任务

### 任务 1：在 PetWindow 中添加右键菜单

<task>
<read_first>
- pet/window.py（当前 PetWindow 实现）
- .planning/phases/02-interaction/02-CONTEXT.md（D-04 菜单项设计）
</read_first>
<action>
在 `pet/window.py` 的 `PetWindow` 类中添加右键菜单功能：

1. 添加导入（在文件顶部）：
```python
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
```

2. 在 PetWindow 类中添加信号和菜单创建：
```python
    # 菜单动作信号（Phase 3+ 连接）
    schedule_requested = Signal()
    chat_requested = Signal()
    settings_requested = Signal()

    def contextMenuEvent(self, event):
        """右键弹出上下文菜单。"""
        menu = QMenu(self)

        schedule_action = QAction("📅 Schedule", self)
        schedule_action.triggered.connect(self.schedule_requested.emit)

        chat_action = QAction("💬 Chat", self)
        chat_action.triggered.connect(self.chat_requested.emit)

        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)

        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(QApplication.quit)

        menu.addAction(schedule_action)
        menu.addAction(chat_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        menu.exec(event.globalPos())
```

3. 添加 QApplication 导入（在文件顶部）：
```python
from PySide6.QtWidgets import QWidget, QMenu, QApplication
```
</action>
<acceptance_criteria>
- `pet/window.py` 包含 `schedule_requested = Signal()`
- `pet/window.py` 包含 `chat_requested = Signal()`
- `pet/window.py` 包含 `settings_requested = Signal()`
- `pet/window.py` 包含 `def contextMenuEvent(self, event):`
- `pet/window.py` 包含 `QMenu(self)`
- `pet/window.py` 包含 `QAction("Schedule", self)` 或类似标签
- `pet/window.py` 包含 `QAction("Chat", self)` 或类似标签
- `pet/window.py` 包含 `QAction("Settings", self)` 或类似标签
- `pet/window.py` 包含 `QAction("Exit", self)` 或类似标签
- `pet/window.py` 包含 `QApplication.quit` 连接到 Exit 动作
- `pet/window.py` 包含 `menu.exec(event.globalPos())`
- `pet/window.py` 包含 `menu.addSeparator()`
</acceptance_criteria>
</task>

---

### 任务 2：在 main.py 中连接菜单信号

<task>
<read_first>
- main.py（当前内容）
- pet/window.py（包含菜单信号）
</read_first>
<action>
在 `main.py` 中，在 `window.clicked.connect(...)` 之后添加菜单信号占位连接：

```python
    # 菜单动作信号占位（Phase 3+ 实现具体功能）
    window.schedule_requested.connect(lambda: print("[Menu] Schedule requested"))
    window.chat_requested.connect(lambda: print("[Menu] Chat requested"))
    window.settings_requested.connect(lambda: print("[Menu] Settings requested"))
```
</action>
<acceptance_criteria>
- `main.py` 包含 `window.schedule_requested.connect(...)`
- `main.py` 包含 `window.chat_requested.connect(...)`
- `main.py` 包含 `window.settings_requested.connect(...)`
- 三个连接使用 lambda 打印日志（占位实现）
</acceptance_criteria>
</task>

---

## 验证

1. **菜单显示验证：** 运行 `python main.py`，右键点击宠物，确认弹出菜单包含 4 个选项
2. **Exit 验证：** 右键菜单中点击 Exit，确认应用退出
3. **信号验证：** 点击 Schedule/Chat/Settings，确认终端打印对应日志
4. **菜单位置验证：** 在屏幕不同位置右键，确认菜单出现在鼠标位置

---

## must_haves

- 使用 `contextMenuEvent` 而非 `mousePressEvent` 检测右键
- 菜单包含 Schedule、Chat、Settings、Exit 四个选项
- Schedule/Chat/Settings 通过 Signal 发射（供 Phase 3+ 连接）
- Exit 使用 `QApplication.quit()` 退出
- Schedule 和 Exit 之间有分隔线（`menu.addSeparator()`）
- 菜单使用 `menu.exec(event.globalPos())` 在鼠标位置显示
