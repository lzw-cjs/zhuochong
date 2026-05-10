"""对话气泡组件：显示在宠物上方的临时文本气泡"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon
from PySide6.QtCore import QPoint


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
        layout.setContentsMargins(0, 0, 0, 8)
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
        bubble_y = anchor_y - self.height() - 4

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

        triangle = QPolygon([
            QPoint(cx - 6, top),
            QPoint(cx + 6, top),
            QPoint(cx, self.height()),
        ])
        painter.drawPolygon(triangle)

        painter.end()
