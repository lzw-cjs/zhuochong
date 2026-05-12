"""屏幕移动控制器：WALK 状态时水獭自主满屏走动"""
import random
from PySide6.QtCore import QObject, QTimer
from pet.states import PetState
from pet.animator import SpriteAnimator
from pet.window import PetWindow


class MovementController(QObject):
    """控制 WALK 状态的屏幕自主移动。"""

    def __init__(self, window: PetWindow, animator: SpriteAnimator):
        super().__init__()
        self._window = window
        self._animator = animator
        self._timer = QTimer()
        self._timer.timeout.connect(self._move_step)
        self._target = None
        self._moving = False
        self._step_count = 0

        animator.state_changed.connect(self._on_state_changed)

    def _on_state_changed(self, state: PetState):
        if state == PetState.WALK:
            self._pick_destination()
            self._timer.start(40)  # 25 FPS 移动
            self._moving = True
        else:
            self._timer.stop()
            self._moving = False

    def _get_sprite_size(self) -> int:
        """获取精灵实际显示尺寸。"""
        return int(self._window.BASE_CANVAS * 1.4 * self._window._scale)

    def _pick_destination(self):
        screen = self._window.screen()
        if screen:
            geo = screen.availableGeometry()
            sprite_size = self._get_sprite_size()
            x = random.randint(geo.left(), geo.right() - sprite_size)
            y = random.randint(geo.top(), geo.bottom() - sprite_size)
            self._target = (x, y)

    def _move_step(self):
        if not self._target:
            self._pick_destination()
            return

        pos = self._window.get_position()
        dx = self._target[0] - pos[0]
        dy = self._target[1] - pos[1]
        dist = (dx ** 2 + dy ** 2) ** 0.5

        # 到达目标附近，换新目标
        if dist < 10:
            self._pick_destination()
            self._step_count += 1
            # 走 3-5 个目标后停下休息
            if self._step_count >= random.randint(3, 5):
                self._animator.set_state(PetState.IDLE)
                self._step_count = 0
            return

        # 移动步进 — 速度 4px/帧
        step = 4
        nx = pos[0] + int(step * dx / dist)
        ny = pos[1] + int(step * dy / dist)

        self._window.set_sprite_position(nx, ny)

    def stop(self):
        self._timer.stop()
        self._moving = False

    @property
    def is_moving(self) -> bool:
        return self._moving
