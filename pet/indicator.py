"""状态头标指示器 — 悬浮在宠物头顶的 emoji，用线连接"""
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPixmap

from pet.states import PetState


class StateIndicator(QWidget):
    """悬浮在宠物头顶的状态指示器，带连接线。"""

    STATE_EMOJI = {
        PetState.IDLE: "",        # 无指示器
        PetState.WALK: "\U0001f463",   # 👣
        PetState.SLEEP: "\U0001f4a4",  # 💤
        PetState.HAPPY: "❤️", # ❤️
        PetState.ALERT: "\U0001f514",  # 🔔
        PetState.EAT: "\U0001f41f",    # 🐟
        PetState.PLAY: "⚽",       # ⚽
        PetState.GROOM: "✨",      # ✨
        PetState.REST: "☀️", # ☀️
    }

    # 基准尺寸（scale=1.0 时）
    BASE_INDICATOR_SIZE = 48
    BASE_LINE_LENGTH = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # 当前缩放和尺寸
        self._scale = 1.0
        self._indicator_size = self.BASE_INDICATOR_SIZE
        self._line_length = self.BASE_LINE_LENGTH

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_window_size()

        self._float_offset = 0
        self._float_dir = 1
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._animate_float)
        self._float_timer.start(400)

        self._current_state = PetState.IDLE
        self._sprite_display_width = 252  # 默认精灵显示宽度
        self.hide()

    def _update_window_size(self):
        """根据缩放更新窗口和标签大小。"""
        self._indicator_size = int(self.BASE_INDICATOR_SIZE * self._scale)
        self._line_length = int(self.BASE_LINE_LENGTH * self._scale)
        total_h = self._indicator_size + self._line_length
        self.setFixedSize(self._indicator_size, total_h)
        self._label.setGeometry(0, 0, self._indicator_size, self._indicator_size)

    def set_scale(self, scale: float):
        """设置缩放倍数，调整指示器大小。"""
        self._scale = scale
        self._update_window_size()
        # 更新 emoji 字体大小
        font_size = int(28 * scale)
        emoji = self.STATE_EMOJI.get(self._current_state, "")
        if emoji:
            self._label.setText(f'<span style="font-size:{font_size}px">{emoji}</span>')
        self.update()

    def set_sprite_width(self, width: int):
        """设置精灵实际显示宽度，用于居中计算。"""
        self._sprite_display_width = width

    def show_for_state(self, state: PetState, anchor_x: int, anchor_y: int,
                       bounce_offset: int = 0, costume_offset_y: int = 0):
        """根据状态显示对应 emoji，IDLE 时隐藏。"""
        self._current_state = state
        emoji = self.STATE_EMOJI.get(state, "")
        if not emoji:
            self.hide()
            return
        font_size = int(28 * self._scale)
        self._label.setText(f'<span style="font-size:{font_size}px">{emoji}</span>')
        self._update_anchor_position(anchor_x, anchor_y, bounce_offset, costume_offset_y)
        self.show()
        self.update()

    def update_position(self, anchor_x: int, anchor_y: int,
                        bounce_offset: int = 0, costume_offset_y: int = 0):
        """跟随宠物位置更新。"""
        if self.isVisible():
            self._update_anchor_position(anchor_x, anchor_y, bounce_offset, costume_offset_y)

    def _update_anchor_position(self, anchor_x: int, anchor_y: int,
                                bounce_offset: int = 0, costume_offset_y: int = 0):
        """定位在 anchor 上方居中 + 浮动偏移。"""
        x = anchor_x + (self._sprite_display_width - self._indicator_size) // 2
        # 弹跳偏移（画布坐标）和服装偏移（画布坐标）需要缩放到显示坐标
        display_bounce = int(bounce_offset * self._scale * 1.4)
        display_costume = int(costume_offset_y * self._scale * 1.4)
        y = (anchor_y - self._indicator_size - self._line_length
             + self._float_offset - display_bounce - display_costume)
        self.move(QPoint(int(x), int(y)))

    def paintEvent(self, event):
        """绘制连接线。"""
        # 先清除为透明（防止黑框闪烁）
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 连接线：从 emoji 底部到窗口底部
        line_color = QColor(200, 200, 200, 180)
        pen = QPen(line_color, max(1, int(2 * self._scale)), Qt.PenStyle.DashLine)
        painter.setPen(pen)

        x = self._indicator_size // 2
        y_start = self._indicator_size - int(4 * self._scale)
        y_end = self._indicator_size + self._line_length
        painter.drawLine(x, y_start, x, y_end)

        # 底部小圆点
        dot_r = max(2, int(3 * self._scale))
        painter.setBrush(QColor(200, 200, 200, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x - dot_r, y_end - dot_r, dot_r * 2, dot_r * 2)

        painter.end()

    def _animate_float(self):
        """上下浮动 2px。"""
        self._float_offset += self._float_dir * 2
        if abs(self._float_offset) >= 4:
            self._float_dir *= -1
        if self.isVisible():
            pos = self.pos()
            self.move(pos.x(), pos.y() + self._float_dir * 2)
