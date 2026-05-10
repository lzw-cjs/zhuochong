---
wave: 2
depends_on:
  - P2.2
  - P2.3
files_modified:
  - pet/tray.py
  - pet/__init__.py
  - main.py
autonomous: true
---

# P2.4 — System Tray Icon

## 目标

实现系统托盘图标：在 Windows 通知区域显示宠物图标，右键菜单提供 Show/Hide 和 Exit 选项，双击切换宠物可见性。使用代码生成的占位图标。

**覆盖需求：** INT-02

---

## 任务

### 任务 1：实现 SystemTray 组件

<task>
<read_first>
- pet/window.py（PetWindow 实现）
- .planning/phases/02-interaction/02-CONTEXT.md（D-05 系统托盘设计）
</read_first>
<action>
创建 `pet/tray.py`，实现系统托盘功能：

```python
"""系统托盘图标与菜单"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt, Signal


def create_placeholder_icon() -> QIcon:
    """生成 16x16 占位托盘图标（棕色圆形 + 黑色眼睛）。"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 身体
    painter.setBrush(QColor(139, 90, 43))
    painter.setPen(QColor(139, 90, 43))
    painter.drawEllipse(2, 3, 12, 12)

    # 眼睛
    painter.setBrush(QColor(0, 0, 0))
    painter.drawEllipse(5, 6, 2, 2)
    painter.drawEllipse(9, 6, 2, 2)

    painter.end()
    return QIcon(pixmap)


class PetTrayIcon(QSystemTrayIcon):
    """系统托盘图标。

    功能：
    - 显示占位图标
    - 右键菜单：Show/Hide Pet, Exit
    - 双击切换宠物可见性
    """

    # 切换宠物可见性信号
    toggle_visibility = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置图标
        self.setIcon(create_placeholder_icon())
        self.setToolTip("Smart Desktop Pet")

        # 右键菜单
        self._menu = QMenu()

        self._toggle_action = QAction("Hide Pet", self)
        self._toggle_action.triggered.connect(self.toggle_visibility.emit)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)

        self._menu.addAction(self._toggle_action)
        self._menu.addSeparator()
        self._menu.addAction(exit_action)

        self.setContextMenu(self._menu)

        # 双击切换可见性
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        """处理托盘图标激活事件。"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility.emit()

    def update_visibility_state(self, is_visible: bool) -> None:
        """更新菜单文本以反映当前可见性状态。"""
        if is_visible:
            self._toggle_action.setText("Hide Pet")
        else:
            self._toggle_action.setText("Show Pet")
```
</action>
<acceptance_criteria>
- `pet/tray.py` 包含 `class PetTrayIcon(QSystemTrayIcon):`
- `pet/tray.py` 包含 `def create_placeholder_icon() -> QIcon:`
- `pet/tray.py` 包含 `toggle_visibility = Signal()`
- `pet/tray.py` 包含 `QAction("Hide Pet", self)`
- `pet/tray.py` 包含 `QAction("Exit", self)`
- `pet/tray.py` 包含 `QApplication.quit` 连接到 Exit
- `pet/tray.py` 包含 `self.activated.connect(self._on_activated)`
- `pet/tray.py` 包含 `QSystemTrayIcon.ActivationReason.DoubleClick` 检测
- `pet/tray.py` 包含 `def update_visibility_state(self, is_visible: bool):`
- `pet/tray.py` 包含 `self.setContextMenu(self._menu)`
- `pet/tray.py` 包含 `self.setToolTip("Smart Desktop Pet")`
- 占位图标绘制棕色圆形 + 黑色眼睛
</acceptance_criteria>
</task>

---

### 任务 2：集成托盘图标到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/tray.py（PetTrayIcon 实现）
- pet/window.py（PetWindow）
</read_first>
<action>
更新 `main.py`，集成系统托盘图标：

1. 添加导入：
```python
from pet.tray import PetTrayIcon
```

2. 在 `window.show()` 之前创建托盘图标：
```python
    # 创建系统托盘图标
    tray = PetTrayIcon()
```

3. 连接托盘信号到窗口可见性切换：
```python
    # 托盘图标切换可见性
    def toggle_pet_visibility():
        if window.isVisible():
            window.hide()
            tray.update_visibility_state(False)
        else:
            window.show()
            tray.update_visibility_state(True)

    tray.toggle_visibility.connect(toggle_pet_visibility)
```

4. 在 `window.show()` 之后显示托盘图标：
```python
    tray.show()
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.tray import PetTrayIcon`
- `main.py` 包含 `tray = PetTrayIcon()`
- `main.py` 包含 `tray.toggle_visibility.connect(toggle_pet_visibility)`
- `main.py` 包含 `tray.show()`
- `main.py` 包含 `window.hide()` 和 `window.show()` 在切换函数中
- `main.py` 包含 `tray.update_visibility_state(...)` 调用
</acceptance_criteria>
</task>

---

### 任务 3：更新 pet/__init__.py 导出

<task>
<read_first>
- pet/__init__.py（当前内容）
- pet/bubble.py（ChatBubble）
- pet/tray.py（PetTrayIcon）
</read_first>
<action>
更新 `pet/__init__.py`，添加新组件导出：

```python
from pet.window import PetWindow
from pet.states import PetState, can_transition
from pet.animator import SpriteAnimator, generate_all_placeholder_frames
from pet.behavior import BehaviorScheduler
from pet.bubble import ChatBubble
from pet.tray import PetTrayIcon

__all__ = [
    "PetWindow",
    "PetState",
    "can_transition",
    "SpriteAnimator",
    "generate_all_placeholder_frames",
    "BehaviorScheduler",
    "ChatBubble",
    "PetTrayIcon",
]
```
</action>
<acceptance_criteria>
- `pet/__init__.py` 包含 `from pet.bubble import ChatBubble`
- `pet/__init__.py` 包含 `from pet.tray import PetTrayIcon`
- `pet/__init__.py` 的 `__all__` 列表包含 `ChatBubble` 和 `PetTrayIcon`
</acceptance_criteria>
</task>

---

## 验证

1. **托盘图标验证：** 运行 `python main.py`，确认 Windows 通知区域出现棕色圆形图标
2. **右键菜单验证：** 右键托盘图标，确认菜单包含 "Hide Pet" 和 "Exit"
3. **双击切换验证：** 双击托盘图标，确认宠物隐藏；再次双击，确认宠物显示
4. **菜单文本更新验证：** 隐藏宠物后右键托盘，确认菜单文本变为 "Show Pet"
5. **Exit 验证：** 从托盘菜单点击 Exit，确认应用退出
6. **Tooltip 验证：** 鼠标悬停托盘图标，确认显示 "Smart Desktop Pet"

---

## must_haves

- 占位图标使用代码生成（16x16 棕色圆形 + 黑色眼睛）
- 托盘右键菜单包含 Show/Hide Pet 和 Exit
- 双击使用 `QSystemTrayIcon.ActivationReason.DoubleClick` 检测
- 菜单文本根据可见性动态更新（Show Pet / Hide Pet）
- Exit 使用 `QApplication.quit()` 退出
- 托盘图标在 `window.show()` 之后调用 `tray.show()`
- `toggle_visibility` 信号连接到可见性切换函数
