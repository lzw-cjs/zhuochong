"""宠物行为调度器：定时随机切换动画状态"""
import random
from PySide6.QtCore import QTimer

from pet.states import PetState
from pet.animator import SpriteAnimator


class BehaviorScheduler:
    """定时随机切换宠物动画状态。

    逻辑：
    - 启动后进入 idle 状态
    - 5 分钟无用户操作 → 自动切换到 sleep
    - 用户交互（Phase 2 实现）→ happy → 10 秒后回到 idle
    - idle 状态下每隔 30-90 秒随机切换到 walk（原地不移动，D-14）
    """

    # 无操作超时时间（毫秒）
    IDLE_TIMEOUT = 5 * 60 * 1000  # 5 分钟
    # 状态恢复超时时间（毫秒）
    RETURN_TIMEOUT = 10 * 1000  # 10 秒
    # idle 随机切换间隔范围（毫秒）
    RANDOM_MIN = 30 * 1000  # 30 秒
    RANDOM_MAX = 90 * 1000  # 90 秒

    def __init__(self, animator: SpriteAnimator):
        self._animator = animator

        # 无操作计时器 → 切换到 sleep
        self._idle_timer = QTimer()
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        # 状态恢复计时器 → 回到 idle
        self._return_timer = QTimer()
        self._return_timer.setSingleShot(True)
        self._return_timer.timeout.connect(self._on_return_timeout)

        # idle 随机切换计时器
        self._random_timer = QTimer()
        self._random_timer.setSingleShot(True)
        self._random_timer.timeout.connect(self._on_random_switch)

    def start(self) -> None:
        """启动行为调度。"""
        self._animator.set_state(PetState.IDLE)
        self._idle_timer.start(self.IDLE_TIMEOUT)
        self._schedule_random_switch()

    def stop(self) -> None:
        """停止所有计时器。"""
        self._idle_timer.stop()
        self._return_timer.stop()
        self._random_timer.stop()

    def on_user_interaction(self) -> None:
        """用户交互时调用（Phase 2 接入）。"""
        self._idle_timer.stop()
        self._random_timer.stop()

        self._animator.set_state(PetState.HAPPY)
        self._return_timer.start(self.RETURN_TIMEOUT)

    def _on_idle_timeout(self) -> None:
        """5 分钟无操作 → 切换到 sleep。"""
        self._random_timer.stop()
        self._animator.set_state(PetState.SLEEP)

    def _on_return_timeout(self) -> None:
        """状态恢复到 idle。"""
        self._animator.set_state(PetState.IDLE)
        self._idle_timer.start(self.IDLE_TIMEOUT)
        self._schedule_random_switch()

    def _on_random_switch(self) -> None:
        """idle 状态下随机切换到 walk。"""
        if self._animator.current_state == PetState.IDLE:
            self._animator.set_state(PetState.WALK)
            # walk 持续 5-10 秒后回到 idle
            walk_duration = random.randint(5000, 10000)
            QTimer.singleShot(walk_duration, self._on_walk_done)

    def _on_walk_done(self) -> None:
        """walk 结束，回到 idle。"""
        if self._animator.current_state == PetState.WALK:
            self._animator.set_state(PetState.IDLE)
            self._schedule_random_switch()

    def _schedule_random_switch(self) -> None:
        """调度下一次随机状态切换。"""
        interval = random.randint(self.RANDOM_MIN, self.RANDOM_MAX)
        self._random_timer.start(interval)
