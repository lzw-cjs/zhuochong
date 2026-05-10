---
wave: 1
depends_on:
  - P3.1
files_modified:
  - pet/chat_panel.py
  - pet/__init__.py
autonomous: true
---

# P3.3 — 聊天面板 UI

## 目标

实现独立的聊天面板窗口：消息列表（用户右对齐、宠物左对齐）、底部输入框 + 发送按钮、像素风配色、可拖动、关闭不退出应用。

**覆盖需求：** INT-03

---

## 任务

### 任务 1：实现 ChatPanel 聊天面板

<task>
<action>
创建 `pet/chat_panel.py`：

```python
"""聊天面板：独立窗口，消息列表 + 输入框"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont


class MessageBubble(QLabel):
    """单条消息气泡。"""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setMaximumWidth(240)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_user:
            self.setStyleSheet("""
                QLabel {
                    background-color: #D4A574;
                    color: #333333;
                    border: 2px solid #A0784C;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: #F5F0E8;
                    color: #333333;
                    border: 2px solid #C0B090;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)


class ChatPanel(QWidget):
    """聊天面板窗口。

    功能：
    - 消息列表（滚动区域）
    - 用户消息右对齐，宠物回复左对齐
    - 底部输入框 + 发送按钮
    - 关闭时隐藏而非退出
    """

    # 用户发送消息信号（外部连接到 ChatEngine）
    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("与宠物聊天")
        self.setFixedSize(QSize(360, 480))
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 标题栏
        title = QLabel("与宠物聊天")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background-color: #8B5A2B;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                border-radius: 6px;
            }
        """)
        layout.addWidget(title)

        # 消息滚动区域
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #C0B090;
                border-radius: 6px;
                background-color: #FDF8F0;
            }
        """)

        # 消息容器
        self._messages_widget = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setSpacing(6)
        self._scroll.setWidget(self._messages_widget)
        layout.addWidget(self._scroll, 1)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("输入消息...")
        self._input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0B090;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border-color: #8B5A2B;
            }
        """)
        self._input.returnPressed.connect(self._on_send)

        self._send_btn = QPushButton("发送")
        self._send_btn.setFixedWidth(60)
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5A2B;
                color: white;
                border: 2px solid #6B4A1B;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A0784C;
            }
            QPushButton:pressed {
                background-color: #6B4A1B;
            }
        """)
        self._send_btn.clicked.connect(self._on_send)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(self._send_btn)
        layout.addLayout(input_layout)

    def _on_send(self) -> None:
        """发送按钮点击或回车。"""
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.add_message(text, is_user=True)
        self.message_sent.emit(text)

    def add_message(self, text: str, is_user: bool) -> None:
        """添加一条消息到列表。

        Args:
            text: 消息文本
            is_user: True 表示用户消息，False 表示宠物回复
        """
        bubble = MessageBubble(text, is_user)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(4, 2, 4, 2)

        if is_user:
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        container = QWidget()
        container.setLayout(wrapper)
        self._messages_layout.addWidget(container)

        # 滚动到底部
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        """关闭时隐藏而非退出。"""
        event.ignore()
        self.hide()
```
</action>
<acceptance_criteria>
- `pet/chat_panel.py` 包含 `class ChatPanel(QWidget):`
- `pet/chat_panel.py` 包含 `class MessageBubble(QLabel):`
- `pet/chat_panel.py` 包含 `message_sent = Signal(str)`
- `pet/chat_panel.py` 包含 `def add_message(self, text: str, is_user: bool):`
- `pet/chat_panel.py` 包含 `def _on_send(self):`
- `pet/chat_panel.py` 包含 `self._input = QLineEdit()`
- `pet/chat_panel.py` 包含 `self._send_btn = QPushButton("发送")`
- `pet/chat_panel.py` 包含 `self._scroll = QScrollArea()`
- `pet/chat_panel.py` 包含 `event.ignore()` + `self.hide()` 在 closeEvent 中
- `pet/chat_panel.py` 包含 `self._input.returnPressed.connect(self._on_send)` 回车发送
- 用户消息右对齐（`wrapper.addStretch()` 在左侧）
- 宠物回复左对齐（`wrapper.addStretch()` 在右侧）
- 配色使用棕色/米色主题
</acceptance_criteria>
</task>

---

### 任务 2：更新 pet/__init__.py

<task>
<action>
更新 `pet/__init__.py`，添加 ChatPanel 导出：

在导入区域添加：
```python
from pet.chat_panel import ChatPanel
```

在 `__all__` 列表中添加：
```python
    "ChatPanel",
```
</action>
<acceptance_criteria>
- `pet/__init__.py` 包含 `from pet.chat_panel import ChatPanel`
- `pet/__init__.py` 的 `__all__` 包含 `ChatPanel`
</acceptance_criteria>
</task>

---

## 验证

1. **面板显示验证：** 创建 ChatPanel 实例并 show()，确认窗口出现
2. **消息显示验证：** 调用 `add_message("测试", True)` 和 `add_message("回复", False)`，确认消息正确对齐
3. **发送验证：** 输入文字点击发送，确认 `message_sent` 信号发射
4. **关闭验证：** 关闭面板窗口，确认面板隐藏而非应用退出

---

## must_haves

- ChatPanel 使用 `WindowStaysOnTopHint | Tool` 窗口标志
- closeEvent 使用 `event.ignore()` + `self.hide()` 隐藏而非退出
- 消息输入框支持回车发送（`returnPressed`）
- 用户消息右对齐，宠物回复左对齐
- 配色使用棕色/米色像素风主题
- 消息气泡最大宽度 240px
- 面板固定尺寸 360x480
