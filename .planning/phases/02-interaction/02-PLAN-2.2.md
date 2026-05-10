---
wave: 1
depends_on:
  - P2.1
files_modified:
  - pet/bubble.py
  - pet/__init__.py
  - main.py
autonomous: true
---

# P2.2 — Click Feedback & Speech Bubble

## 目标

实现点击宠物时的视觉反馈：宠物切换到 happy 状态（通过 BehaviorScheduler），同时在宠物上方显示一个临时对话气泡（ChatBubble），3 秒后自动消失。

**覆盖需求：** PET-04

---

## 任务

### 任务 1：实现 ChatBubble 气泡组件

<task>
<read_first>
- pet/window.py（PetWindow 实现，了解窗口结构）
- .planning/phases/02-interaction/02-CONTEXT.md（D-03 ChatBubble 设计）
</read_first>
<action>
创建 `pet/bubble.py`，实现 ChatBubble 组件：

```python
"""对话气泡组件：显示在宠物上方的临时文本气泡"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont


class ChatBubble(QWidget):
    """临时对话气泡，显示在宠物窗口上方。

    特性：
    - 自动锚定在目标窗口上方
    - 3 秒后自动消失
    - 半透明白色背景 + 圆角
    - 最大宽度 200px，自动换行
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 无边框、透明背景、不在任务栏显示
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # 标签
        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(180)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 样式
        self._label.setStyleSheet("""
            QLabel {
                color: #333333;
                background-color: rgba(255, 255, 255, 220);
                border: 2px solid #888888;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 11px;
            }
        """)

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)  # 底部留白给气泡尾巴
        layout.addWidget(self._label)

        # 自动消失计时器
        self._dismiss_timer = QTimer()
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.hide)

    def show_message(self, text: str, anchor_x: int, anchor_y: int, duration_ms: int = 3000) -> None:
        """显示气泡消息。

        Args:
            text: 要显示的文本
            anchor_x: 锚定点 x 坐标（宠物窗口中心 x）
            anchor_y: 锚定点 y 坐标（宠物窗口顶部 y）
            duration_ms: 显示持续时间（毫秒），默认 3 秒
        """
        self._label.setText(text)
        self.adjustSize()

        # 定位：气泡底部居中对齐到锚定点上方
        bubble_x = anchor_x - self.width() // 2
        bubble_y = anchor_y - self.height() - 4  # 4px 间距

        self.move(bubble_x, bubble_y)
        self.show()

        # 重启计时器
        self._dismiss_timer.start(duration_ms)

    def paintEvent(self, event):
        """绘制气泡尾巴（小三角指向下方）。"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 气泡尾巴：底部中心的小三角
        cx = self.width() // 2
        top = self.height() - 8

        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(QPen(QColor(136, 136, 136), 2))

        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint
        triangle = QPolygon([
            QPoint(cx - 6, top),
            QPoint(cx + 6, top),
            QPoint(cx, self.height()),
        ])
        painter.drawPolygon(triangle)

        painter.end()
```
</action>
<acceptance_criteria>
- `pet/bubble.py` 包含 `class ChatBubble(QWidget):`
- `pet/bubble.py` 包含 `Qt.WindowType.FramelessWindowHint`
- `pet/bubble.py` 包含 `Qt.WindowType.WindowStaysOnTopHint`
- `pet/bubble.py` 包含 `Qt.WindowType.Tool`
- `pet/bubble.py` 包含 `Qt.WidgetAttribute.WA_TranslucentBackground`
- `pet/bubble.py` 包含 `def show_message(self, text, anchor_x, anchor_y, duration_ms):`
- `pet/bubble.py` 包含 `self._dismiss_timer = QTimer()`
- `pet/bubble.py` 包含 `self._dismiss_timer.setSingleShot(True)`
- `pet/bubble.py` 包含 `self._label.setMaximumWidth(180)`
- `pet/bubble.py` 包含 `self._label.setWordWrap(True)`
- `pet/bubble.py` 包含气泡尾巴绘制（QPolygon 三角形）
</acceptance_criteria>
</task>

---

### 任务 2：集成气泡到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/bubble.py（ChatBubble 实现）
- pet/window.py（PetWindow，clicked 信号）
</read_first>
<action>
更新 `main.py`，集成 ChatBubble：

1. 添加导入：
```python
from pet.bubble import ChatBubble
```

2. 在 `window.show()` 之前创建气泡实例：
```python
    # 创建对话气泡
    bubble = ChatBubble()
```

3. 修改 `window.clicked.connect` 的连接，同时触发气泡显示：
```python
    # 点击宠物触发交互反馈 + 气泡显示
    def on_pet_clicked():
        behavior.on_user_interaction()
        # 气泡锚定在宠物上方
        pos = window.get_position()
        bubble.show_message("Hello!", pos[0] + 16, pos[1])

    window.clicked.connect(on_pet_clicked)
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.bubble import ChatBubble`
- `main.py` 包含 `bubble = ChatBubble()`
- `main.py` 包含 `window.clicked.connect(on_pet_clicked)`
- `main.py` 包含 `bubble.show_message("Hello!", ...)` 在点击回调中
- `main.py` 包含 `behavior.on_user_interaction()` 在点击回调中
- 气泡实例在 `window.show()` 之前创建
</acceptance_criteria>
</task>

---

## 验证

1. **气泡显示验证：** 运行 `python main.py`，点击宠物，确认：
   - 宠物切换到 happy 状态（嘴巴张开、弹跳）
   - 宠物上方出现白色圆角气泡，显示 "Hello!"
   - 气泡 3 秒后自动消失
2. **气泡位置验证：** 拖动宠物到不同位置，点击确认气泡始终出现在宠物正上方
3. **多次点击验证：** 连续快速点击，确认气泡正确更新位置和重置计时器

---

## must_haves

- ChatBubble 使用 `FramelessWindowHint | WindowStaysOnTopHint | Tool` 三个窗口标志
- ChatBubble 使用 `WA_TranslucentBackground` 实现透明背景
- 气泡自动消失计时器使用 `setSingleShot(True)`
- 气泡定位在宠物窗口上方（`anchor_y - height - 4`）
- 气泡最大宽度 180px（加上 padding 共约 200px）
- 气泡尾巴使用 QPolygon 绘制三角形
- 点击回调同时触发 `behavior.on_user_interaction()` 和气泡显示
