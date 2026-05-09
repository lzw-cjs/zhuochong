"""精灵动画引擎：Sprite 帧管理和动画控制"""
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt

from pet.states import PetState, FRAME_INTERVALS, can_transition

# ============================================================
# 占位素材生成
# ============================================================

def generate_placeholder_frame(state: PetState, frame_index: int, total_frames: int) -> QPixmap:
    """为指定状态和帧索引生成 32x32 占位树懒图。

    每个状态有不同的视觉表现：
    - idle: 棕色椭圆身体 + 黑色眼睛 + 爪子线条（挂在树枝上）
    - walk: 类似 idle，但爪子位置随帧变化（模拟行走）
    - sleep: 闭眼（横线代替圆眼），身体略微缩小（蜷缩）
    - happy: 身体略微膨胀，嘴巴张开（小圆弧）
    - alert: 抖动身体 + 大眼睛 + 红色感叹号

    所有帧的差异确保动画循环可被肉眼分辨。
    """
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # 颜色定义
    body_color = QColor(139, 90, 43)   # 棕色
    eye_color = QColor(0, 0, 0)        # 黑色
    highlight = QColor(180, 120, 60)   # 浅棕（高光）

    if state == PetState.IDLE:
        # 身体 - 椭圆，随帧微微上下浮动
        offset_y = frame_index % 2  # 0, 1, 0, 1...
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(8, 10 + offset_y, 16, 18)

        # 眼睛 - 两个小圆
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(12, 14 + offset_y, 3, 3)
        painter.drawEllipse(19, 14 + offset_y, 3, 3)

        # 爪子 - 上方树枝
        painter.setPen(QPen(QColor(100, 60, 20), 2))
        painter.drawLine(6, 8, 26, 8)  # 树枝
        painter.setPen(QPen(body_color, 2))
        painter.drawLine(10, 10 + offset_y, 8, 6)   # 左爪
        painter.drawLine(22, 10 + offset_y, 24, 6)  # 右爪

    elif state == PetState.WALK:
        # 身体 - 随帧左右摆动模拟行走
        offset_x = (frame_index % 3) - 1  # -1, 0, 1, -1...
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(8 + offset_x, 10, 16, 18)

        # 眼睛
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(12 + offset_x, 14, 3, 3)
        painter.drawEllipse(19 + offset_x, 14, 3, 3)

        # 爪子 - 交替前后摆动
        painter.setPen(QPen(body_color, 2))
        if frame_index % 2 == 0:
            painter.drawLine(8 + offset_x, 20, 4, 24)
            painter.drawLine(24 + offset_x, 20, 28, 22)
        else:
            painter.drawLine(8 + offset_x, 20, 4, 22)
            painter.drawLine(24 + offset_x, 20, 28, 24)

    elif state == PetState.SLEEP:
        # 身体 - 蜷缩（略小）
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(9, 12, 14, 16)

        # 闭眼 - 横线
        painter.setPen(QPen(eye_color, 1))
        painter.drawLine(11, 16, 14, 16)
        painter.drawLine(18, 16, 21, 16)

        # Z 字（呼吸起伏动画，每帧位置不同）
        z_offsets = [(22, 8), (24, 6), (26, 4), (22, 8)]
        zx, zy = z_offsets[frame_index % len(z_offsets)]
        painter.setPen(QPen(QColor(100, 150, 255), 1))
        painter.drawText(zx, zy, "z")

    elif state == PetState.HAPPY:
        # 身体 - 开心膨胀
        bounce = frame_index % 2  # 弹跳
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(7, 9 - bounce, 18, 19)

        # 眯眼（弧线）
        painter.setPen(QPen(eye_color, 1))
        painter.drawLine(11, 14 - bounce, 14, 13 - bounce)
        painter.drawLine(11, 14 - bounce, 14, 15 - bounce)
        painter.drawLine(18, 13 - bounce, 21, 14 - bounce)
        painter.drawLine(18, 15 - bounce, 21, 14 - bounce)

        # 嘴巴 - 张开的小圆弧
        painter.setBrush(QBrush(QColor(200, 80, 80)))
        painter.drawChord(13, 18 - bounce, 6, 4, 0, 180 * 16)

    elif state == PetState.ALERT:
        # 抖动效果：奇偶帧交替偏移
        shake = (frame_index % 2) * 2 - 1  # -1, 1, -1, 1

        # 身体 - 棕色椭圆，左右抖动
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(8 + shake, 10, 16, 18)

        # 大眼睛（4x4，比正常更大表示警觉）
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(11 + shake, 13, 4, 4)
        painter.drawEllipse(18 + shake, 13, 4, 4)

        # 感叹号 - 红色
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawText(14, 8, "!")

    painter.end()
    return pixmap


def generate_all_placeholder_frames() -> dict[PetState, list[QPixmap]]:
    """为所有 5 个状态生成占位帧序列。"""
    frame_counts = {
        PetState.IDLE: 4,
        PetState.WALK: 6,
        PetState.SLEEP: 4,
        PetState.HAPPY: 4,
        PetState.ALERT: 4,
    }
    frames = {}
    for state, count in frame_counts.items():
        state_frames = []
        for i in range(count):
            state_frames.append(generate_placeholder_frame(state, i, count))
        frames[state] = state_frames
    return frames


# ============================================================
# SpriteAnimator
# ============================================================

class SpriteAnimator:
    """精灵帧动画控制器。

    管理各状态的帧序列，使用 QTimer 驱动帧循环。
    外部通过 set_state() 切换动画状态，通过 current_pixmap() 获取当前帧。
    """

    def __init__(self):
        self._frames: dict[PetState, list[QPixmap]] = {}
        self._current_state = PetState.IDLE
        self._current_frame = 0

        # 帧循环定时器
        self._timer = QTimer()
        self._timer.timeout.connect(self._advance_frame)

    def load_frames(self, frames: dict[PetState, list[QPixmap]]) -> None:
        """加载各状态的帧序列。"""
        self._frames = frames

    def set_state(self, state: PetState) -> bool:
        """切换动画状态。

        返回 True 表示切换成功，False 表示不允许的转换。
        """
        if state == self._current_state:
            return True  # 已经是目标状态

        if not can_transition(self._current_state, state):
            return False  # 不允许的转换

        self._current_state = state
        self._current_frame = 0

        # 更新帧间隔
        interval = FRAME_INTERVALS.get(state, 500)
        self._timer.setInterval(interval)

        return True

    def start(self) -> None:
        """启动帧循环。"""
        if not self._frames:
            return
        interval = FRAME_INTERVALS.get(self._current_state, 500)
        self._timer.start(interval)

    def stop(self) -> None:
        """停止帧循环。"""
        self._timer.stop()

    def current_pixmap(self) -> QPixmap | None:
        """获取当前帧的 QPixmap。"""
        frames = self._frames.get(self._current_state)
        if not frames:
            return None
        return frames[self._current_frame]

    @property
    def current_state(self) -> PetState:
        return self._current_state

    def _advance_frame(self) -> None:
        """前进到下一帧（由 QTimer 调用）。"""
        frames = self._frames.get(self._current_state)
        if frames:
            self._current_frame = (self._current_frame + 1) % len(frames)
