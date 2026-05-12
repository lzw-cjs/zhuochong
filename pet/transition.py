"""状态切换的 alpha 渐变过渡动画"""
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter

from pet.states import PetState


class TransitionAnimator(QObject):
    """状态切换时的 300ms alpha 混合过渡。"""

    frame_ready = Signal(QPixmap)
    transition_complete = Signal()

    STEP_MS = 30  # 每步 30ms
    TOTAL_STEPS = 10  # 300ms / 30ms = 10 步

    def __init__(self, parent=None):
        super().__init__()
        self._from_pixmap: QPixmap | None = None
        self._to_pixmap: QPixmap | None = None
        self._current_step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._blend_step)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def start_transition(self, from_pixmap: QPixmap, to_pixmap: QPixmap, duration_ms: int = 300):
        """启动从 from_pixmap 到 to_pixmap 的 alpha 渐变。"""
        if from_pixmap is None or to_pixmap is None:
            self.transition_complete.emit()
            return

        self._from_pixmap = from_pixmap
        self._to_pixmap = to_pixmap
        self._current_step = 0
        steps = max(1, duration_ms // self.STEP_MS)
        self._total_steps = steps
        self._active = True
        self._timer.start(self.STEP_MS)

    def interrupt(self):
        """中断过渡（ALERT 可中断任何过渡）。"""
        self._timer.stop()
        self._active = False
        if self._to_pixmap:
            self.frame_ready.emit(self._to_pixmap)
        self.transition_complete.emit()

    def _blend_step(self):
        """每步混合两帧，alpha 从 0→1 线性插值。"""
        self._current_step += 1
        alpha = self._current_step / self._total_steps

        if alpha >= 1.0:
            self._timer.stop()
            self._active = False
            self.frame_ready.emit(self._to_pixmap)
            self.transition_complete.emit()
            return

        blended = self._blend_pixmaps(self._from_pixmap, self._to_pixmap, alpha)
        self.frame_ready.emit(blended)

    @staticmethod
    def _blend_pixmaps(bottom: QPixmap, top: QPixmap, alpha: float) -> QPixmap:
        """用 QPainter.setOpacity 混合两张 QPixmap。"""
        if bottom is None or bottom.isNull():
            return top if top is not None and not top.isNull() else QPixmap()
        if top is None or top.isNull():
            return bottom

        w = max(bottom.width(), top.width())
        h = max(bottom.height(), top.height())
        if w <= 0 or h <= 0:
            return top if not top.isNull() else bottom

        result = QPixmap(w, h)
        result.fill(0)  # transparent

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 绘制旧帧（alpha 递减）
        painter.setOpacity(1.0 - alpha)
        painter.drawPixmap(0, 0, bottom)

        # 绘制新帧（alpha 递增）
        painter.setOpacity(alpha)
        painter.drawPixmap(0, 0, top)

        painter.end()
        return result
