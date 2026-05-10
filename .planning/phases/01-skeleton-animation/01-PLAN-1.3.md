---
wave: 1
depends_on:
  - P1.1
files_modified:
  - pet/states.py
  - pet/animator.py
  - pet/behavior.py
  - pet/__init__.py
  - main.py
autonomous: true
---

# P1.3 — Sprite 动画引擎

## 目标

实现精灵动画系统：PetState 枚举与状态转换表、SpriteAnimator（QPixmap + QTimer 帧循环）、AnimationController 状态机、占位素材生成、BehaviorScheduler 定时状态切换。

**覆盖需求：** PET-03

---

## 任务

### 任务 1：实现 PetState 枚举与转换表

<task>
<read_first>
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 2 节：状态机设计参考实现）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-04 动画状态列表）
</read_first>
<action>
在 `pet/states.py` 中实现状态枚举和转换表：

```python
"""宠物动画状态定义与状态转换表"""
from enum import Enum


class PetState(Enum):
    """宠物动画状态枚举。"""
    IDLE = "idle"       # 挂在树枝上（慢悠悠）
    WALK = "walk"       # 缓慢爬行
    SLEEP = "sleep"     # 蜷缩睡觉
    HAPPY = "happy"     # 开心摇晃


# 状态转换表：当前状态 -> 允许的目标状态列表
TRANSITIONS: dict[PetState, list[PetState]] = {
    PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY],
    PetState.WALK:  [PetState.IDLE, PetState.HAPPY],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY],
    PetState.HAPPY: [PetState.IDLE],
}

# 各状态的帧间隔（毫秒）
FRAME_INTERVALS: dict[PetState, int] = {
    PetState.IDLE:  500,   # 慢悠悠挂在树枝上
    PetState.WALK:  300,   # 缓慢爬行
    PetState.SLEEP: 800,   # 蜷缩呼吸起伏
    PetState.HAPPY: 200,   # 开心摇晃（最快）
}


def can_transition(current: PetState, target: PetState) -> bool:
    """检查从 current 状态是否可以转换到 target 状态。"""
    return target in TRANSITIONS.get(current, [])
```
</action>
<acceptance_criteria>
- `pet/states.py` 包含 `class PetState(Enum):`
- `pet/states.py` 包含四个状态值：`IDLE = "idle"`, `WALK = "walk"`, `SLEEP = "sleep"`, `HAPPY = "happy"`
- `pet/states.py` 包含 `TRANSITIONS: dict[PetState, list[PetState]]`
- `pet/states.py` 包含 `FRAME_INTERVALS: dict[PetState, int]`
- `pet/states.py` 包含 `def can_transition(current: PetState, target: PetState) -> bool:`
- FRAME_INTERVALS 中 IDLE=500, WALK=300, SLEEP=800, HAPPY=200
</acceptance_criteria>
</task>

---

### 任务 2：实现占位素材生成器

<task>
<read_first>
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 3 节：占位素材生成参考实现）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-01 32x32 像素，D-02 树懒，D-03 占位素材）
- pet/states.py（PetState 枚举）
</read_first>
<action>
在 `pet/animator.py` 中先实现占位素材生成函数（与 SpriteAnimator 同一文件）：

```python
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

        # 眼睛 - 眯眼（弧线）
        painter.setPen(QPen(eye_color, 1))
        painter.drawLine(11, 14 - bounce, 14, 13 - bounce)
        painter.drawLine(11, 14 - bounce, 14, 15 - bounce)
        painter.drawLine(18, 13 - bounce, 21, 14 - bounce)
        painter.drawLine(18, 15 - bounce, 21, 14 - bounce)

        # 嘴巴 - 张开的小圆弧
        painter.setBrush(QBrush(QColor(200, 80, 80)))
        painter.drawChord(13, 18 - bounce, 6, 4, 0, 180 * 16)

    painter.end()
    return pixmap


def generate_all_placeholder_frames() -> dict[PetState, list[QPixmap]]:
    """为所有 4 个状态生成占位帧序列。"""
    frame_counts = {
        PetState.IDLE: 4,
        PetState.WALK: 6,
        PetState.SLEEP: 4,
        PetState.HAPPY: 4,
    }
    frames = {}
    for state, count in frame_counts.items():
        state_frames = []
        for i in range(count):
            state_frames.append(generate_placeholder_frame(state, i, count))
        frames[state] = state_frames
    return frames
```
</action>
<acceptance_criteria>
- `pet/animator.py` 包含 `def generate_placeholder_frame(state: PetState, frame_index: int, total_frames: int) -> QPixmap:`
- `pet/animator.py` 包含 `def generate_all_placeholder_frames() -> dict[PetState, list[QPixmap]]:`
- `pet/animator.py` 包含 `pixmap.fill(Qt.GlobalColor.transparent)`（透明背景）
- `pet/animator.py` 包含 `QPainter.RenderHint.Antialiasing, False`（像素风关闭抗锯齿）
- `pet/animator.py` 包含对 PetState.IDLE、WALK、SLEEP、HAPPY 四个分支的处理
- SLEEP 分支包含闭眼横线（`drawLine` 代替 `drawEllipse`）
- HAPPY 分支包含弹跳效果（`bounce = frame_index % 2`）
- frame_counts 字典中 IDLE=4, WALK=6, SLEEP=4, HAPPY=4
</acceptance_criteria>
</task>

---

### 任务 3：实现 SpriteAnimator

<task>
<read_first>
- pet/animator.py（当前内容，含占位素材生成器）
- pet/states.py（PetState 枚举、FRAME_INTERVALS）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 2 节：SpriteAnimator 参考实现）
</read_first>
<action>
在 `pet/animator.py` 中，在占位素材生成函数之后，添加 `SpriteAnimator` 类：

```python
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
```
</action>
<acceptance_criteria>
- `pet/animator.py` 包含 `class SpriteAnimator:`
- `pet/animator.py` 包含 `def load_frames(self, frames: dict[PetState, list[QPixmap]]) -> None:`
- `pet/animator.py` 包含 `def set_state(self, state: PetState) -> bool:`
- `pet/animator.py` 包含 `def start(self) -> None:`
- `pet/animator.py` 包含 `def stop(self) -> None:`
- `pet/animator.py` 包含 `def current_pixmap(self) -> QPixmap | None:`
- `pet/animator.py` 包含 `def _advance_frame(self) -> None:`
- `pet/animator.py` 包含 `self._timer = QTimer()`
- `pet/animator.py` 包含 `self._timer.timeout.connect(self._advance_frame)`
- `pet/animator.py` 包含 `self._current_frame = (self._current_frame + 1) % len(frames)`
- `set_state` 方法调用 `can_transition()` 检查合法性
</acceptance_criteria>
</task>

---

### 任务 4：实现 BehaviorScheduler

<task>
<read_first>
- pet/animator.py（SpriteAnimator 类）
- pet/states.py（PetState 枚举）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 5 节：BehaviorScheduler 参考实现）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-14 原地切换，D-15 定时随机切换）
</read_first>
<action>
在 `pet/behavior.py` 中实现 BehaviorScheduler：

```python
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
```
</action>
<acceptance_criteria>
- `pet/behavior.py` 包含 `class BehaviorScheduler:`
- `pet/behavior.py` 包含 `IDLE_TIMEOUT = 5 * 60 * 1000`（5 分钟）
- `pet/behavior.py` 包含 `RETURN_TIMEOUT = 10 * 1000`（10 秒）
- `pet/behavior.py` 包含 `def start(self) -> None:`
- `pet/behavior.py` 包含 `def stop(self) -> None:`
- `pet/behavior.py` 包含 `def on_user_interaction(self) -> None:`
- `pet/behavior.py` 包含 `self._animator.set_state(PetState.SLEEP)`（超时后切到 sleep）
- `pet/behavior.py` 包含 `self._animator.set_state(PetState.HAPPY)`（交互后切到 happy）
- `pet/behavior.py` 包含 `random.randint` 用于随机间隔
- `pet/behavior.py` 包含三个 QTimer：`_idle_timer`, `_return_timer`, `_random_timer`
</acceptance_criteria>
</task>

---

### 任务 5：集成动画引擎到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/animator.py（SpriteAnimator + 占位素材生成）
- pet/behavior.py（BehaviorScheduler）
- pet/window.py（PetWindow）
</read_first>
<action>
更新 `main.py`，集成 SpriteAnimator 和 BehaviorScheduler：

```python
"""Smart Desktop Pet — 应用入口"""
import os
import sys

# Win11 RHI 渲染修复：强制使用 OpenGL 后端
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

from data.settings import Settings
from pet.window import PetWindow
from pet.animator import SpriteAnimator, generate_all_placeholder_frames
from pet.behavior import BehaviorScheduler


def main():
    # DPI 感知设置：避免高 DPI 下宠物位置偏移
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 加载设置
    settings = Settings.load()

    # 创建精灵动画器
    animator = SpriteAnimator()
    animator.load_frames(generate_all_placeholder_frames())

    # 创建宠物窗口
    window = PetWindow()
    window.move_to(settings.pet_x, settings.pet_y)

    # 绑定动画器到窗口：定时刷新窗口显示当前帧
    def update_display():
        pixmap = animator.current_pixmap()
        if pixmap:
            window.set_pixmap(pixmap)

    display_timer = QTimer()
    display_timer.timeout.connect(update_display)
    display_timer.start(50)  # 20 FPS 刷新率

    # 启动动画
    animator.start()

    # 创建行为调度器
    behavior = BehaviorScheduler(animator)
    behavior.start()

    # 智能置顶检测
    topmost_timer = QTimer()
    topmost_timer.timeout.connect(window.check_smart_topmost)
    topmost_timer.start(2000)

    window.show()

    print(f"[SmartDesktopPet] 启动完成")
    print(f"  位置: ({settings.pet_x}, {settings.pet_y})")
    print(f"  状态: {settings.pet_state}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.animator import SpriteAnimator, generate_all_placeholder_frames`
- `main.py` 包含 `from pet.behavior import BehaviorScheduler`
- `main.py` 包含 `animator = SpriteAnimator()`
- `main.py` 包含 `animator.load_frames(generate_all_placeholder_frames())`
- `main.py` 包含 `animator.start()`
- `main.py` 包含 `behavior = BehaviorScheduler(animator)`
- `main.py` 包含 `behavior.start()`
- `main.py` 包含 `display_timer = QTimer()` 和 `display_timer.start(50)`
- `main.py` 包含 `window.set_pixmap(pixmap)` 在 update_display 回调中
</acceptance_criteria>
</task>

---

### 任务 6：更新 pet/__init__.py 导出

<task>
<read_first>
- pet/__init__.py（当前内容）
- pet/states.py（PetState）
- pet/animator.py（SpriteAnimator）
- pet/behavior.py（BehaviorScheduler）
- pet/window.py（PetWindow）
</read_first>
<action>
更新 `pet/__init__.py`：

```python
from pet.window import PetWindow
from pet.states import PetState, can_transition
from pet.animator import SpriteAnimator, generate_all_placeholder_frames
from pet.behavior import BehaviorScheduler

__all__ = [
    "PetWindow",
    "PetState",
    "can_transition",
    "SpriteAnimator",
    "generate_all_placeholder_frames",
    "BehaviorScheduler",
]
```
</action>
<acceptance_criteria>
- `pet/__init__.py` 包含 `from pet.states import PetState, can_transition`
- `pet/__init__.py` 包含 `from pet.animator import SpriteAnimator, generate_all_placeholder_frames`
- `pet/__init__.py` 包含 `from pet.behavior import BehaviorScheduler`
- `pet/__init__.py` 包含 `__all__` 列表
</acceptance_criteria>
</task>

---

## 验证

1. **模块导入验证：** 运行 `python -c "from pet.states import PetState; from pet.animator import SpriteAnimator; from pet.behavior import BehaviorScheduler; print('OK')"` 确认所有模块可导入
2. **状态机验证：** 运行以下脚本确认状态转换正确：
   ```python
   from pet.states import PetState, can_transition
   assert can_transition(PetState.IDLE, PetState.WALK)
   assert can_transition(PetState.IDLE, PetState.SLEEP)
   assert not can_transition(PetState.SLEEP, PetState.WALK)  # 不允许
   print("State machine OK")
   ```
3. **占位素材验证：** 运行以下脚本确认素材生成正常：
   ```python
   from pet.animator import generate_all_placeholder_frames
   frames = generate_all_placeholder_frames()
   assert len(frames) == 4, f"Expected 4 states, got {len(frames)}"
   assert len(frames[PetState.IDLE]) == 4, "IDLE should have 4 frames"
   assert len(frames[PetState.WALK]) == 6, "WALK should have 6 frames"
   print("Placeholder frames OK")
   ```
4. **完整启动验证：** 运行 `python main.py`，确认：
   - 窗口中可以看到树懒动画在循环播放
   - 动画状态自动切换（idle → walk → idle → ... → sleep）
   - 5 分钟无操作后自动切换到 sleep 状态
   - 窗口透明、无边框、不在任务栏中

---

## must_haves

- PetState 包含 IDLE、WALK、SLEEP、HAPPY 四个状态
- 转换表禁止 SLEEP → WALK 直接转换（必须经过 IDLE）
- 占位素材每个状态有不同帧数（IDLE=4, WALK=6, SLEEP=4, HAPPY=4）
- 占位素材使用透明背景（`Qt.GlobalColor.transparent`）
- 占位素材关闭抗锯齿（`Antialiasing, False`）
- SpriteAnimator 使用 `QTimer.timeout` 驱动帧循环
- 帧索引使用取模运算循环：`(self._current_frame + 1) % len(frames)`
- BehaviorScheduler 使用三个独立的 `QTimer`（idle、return、random）
- 所有 QTimer 设置为 `setSingleShot(True)`
- BehaviorScheduler.start() 设置初始状态为 IDLE
