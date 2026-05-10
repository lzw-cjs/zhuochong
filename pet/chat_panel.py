"""聊天面板：独立窗口，消息列表 + 输入框"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QSize


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
    """聊天面板窗口。"""

    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("与宠物聊天")
        self.setFixedSize(QSize(360, 480))
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

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
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.add_message(text, is_user=True)
        self.message_sent.emit(text)

    def add_message(self, text: str, is_user: bool) -> None:
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
        event.ignore()
        self.hide()
