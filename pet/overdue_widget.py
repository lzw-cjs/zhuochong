"""超时未完成通知：在屏幕上循环移动的浮动通知"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QScreen, QGuiApplication


class OverdueWidget(QWidget):
    """超时未完成事件的浮动通知。

    在屏幕上来回移动，直到用户延长完成时间或取消事件。
    """

    def __init__(self, event_title: str, on_extend, on_cancel, parent=None):
        super().__init__(parent)
        self._event_title = event_title
        self._on_extend = on_extend
        self._on_cancel = on_cancel

        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(320, 100)

        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        # 标题
        title = QLabel(f"⏰ 未完成: {event_title}")
        title.setStyleSheet("""
            QLabel {
                color: #D94A4A;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
        """)
        layout.addWidget(title)

        # 提示
        hint = QLabel("请延长完成时间或取消日程")
        hint.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
        layout.addWidget(hint)

        # 按钮
        btn_layout = QHBoxLayout()
        extend_btn = QPushButton("延长时间")
        extend_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9; color: white;
                border: 1px solid #3A70B9; border-radius: 4px;
                padding: 4px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #5AA0E9; }
        """)
        extend_btn.clicked.connect(self._handle_extend)

        cancel_btn = QPushButton("取消日程")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #D94A4A; color: white;
                border: 1px solid #B93A3A; border-radius: 4px;
                padding: 4px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #E95A5A; }
        """)
        cancel_btn.clicked.connect(self._handle_cancel)

        dismiss_btn = QPushButton("知道了")
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #888; color: white;
                border: 1px solid #666; border-radius: 4px;
                padding: 4px 12px; font-size: 11px;
            }
        """)
        dismiss_btn.clicked.connect(self.close)

        btn_layout.addWidget(extend_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(dismiss_btn)
        layout.addLayout(btn_layout)

        # 背景样式
        self.setStyleSheet("""
            OverdueWidget {
                background-color: rgba(255, 240, 240, 230);
                border: 2px solid #D94A4A;
                border-radius: 10px;
            }
        """)

        # 移动动画
        self._direction = 1  # 1=右, -1=左
        self._speed = 2
        self._move_timer = QTimer()
        self._move_timer.timeout.connect(self._move_step)
        self._move_timer.start(30)

    def _move_step(self):
        """每步移动。"""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        pos = self.pos()

        new_x = pos.x() + self._speed * self._direction
        if new_x + self.width() > geo.right():
            self._direction = -1
        elif new_x < geo.left():
            self._direction = 1

        self.move(new_x, pos.y())

    def _handle_extend(self):
        self._move_timer.stop()
        self._on_extend(self._event_title)
        self.close()

    def _handle_cancel(self):
        self._move_timer.stop()
        self._on_cancel(self._event_title)
        self.close()

    def closeEvent(self, event):
        self._move_timer.stop()
        super().closeEvent(event)
