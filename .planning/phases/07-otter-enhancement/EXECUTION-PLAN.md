# Execution Plan — 水獭宠物功能扩展 (Phase 7)

> 可在新会话中逐 Phase 执行的 LLM 友好计划。

---

## Phase 0: Allowed APIs & Anti-Patterns

### Allowed PySide6 APIs (verified in codebase)

**QPainter** (from `pet/animator.py`):
- `QPainter(QPixmap)`, `setRenderHint(Antialiasing, False)`
- `setBrush(QBrush(QColor))`, `setPen(QPen(QColor, width))`
- `drawEllipse(x, y, w, h)`, `drawLine(x1, y1, x2, y2)`
- `drawText(x, y, str)`, `drawChord(x, y, w, h, start, span)`
- `drawRect(x, y, w, h)`, `drawRoundedRect(x, y, w, h, xr, yr)`
- `setOpacity(float)` — 用于过渡动画
- `end()` — 必须调用

**QTransform**:
- `QTransform().scale(-1, 1)` — 水平翻转精灵（WALK 朝向）

**Signals** (from `pet/window.py`):
- `position_changed = Signal(int, int)` — line 23
- `clicked = Signal()` — line 25

**SpriteAnimator** (from `pet/animator.py`):
- `load_frames(frames: dict[PetState, list[QPixmap]])` — line 171
- `set_state(state: PetState) -> bool` — line 175
- `current_pixmap() -> QPixmap | None` — line 206
- `current_state` (property) — line 213

**BehaviorScheduler** (from `pet/behavior.py`):
- `__init__(animator: SpriteAnimator)` — line 27
- `start()`, `stop()`, `on_user_interaction()` — lines 45-62

**ChatBubble pattern** (from `pet/bubble.py`):
- `show_message(text, anchor_x, anchor_y, duration_ms=3000)` — line 58
- 定位：`bubble_x = anchor_x - width//2`, `bubble_y = anchor_y - height - 4`
- 窗口标志：`FramelessWindowHint | WindowStaysOnTopHint | Tool`

**main.py wiring** (lines 60-67):
```python
def update_display():
    pixmap = animator.current_pixmap()
    if pixmap:
        window.set_pixmap(pixmap)
display_timer = QTimer()
display_timer.timeout.connect(update_display)
display_timer.start(50)  # 20 FPS
```

### Anti-Patterns
- ❌ 不要假设 `QPainter` 有 `drawPixmap` 以外的图片加载方法
- ❌ 不要在 `__init__` 中设置 `WA_TranslucentBackground`（Win11 RHI 问题，要在 `showEvent` 中设置）
- ❌ 不要直接用 `os.rename()`（Windows 不原子），用 `os.replace()`
- ❌ 不要修改 `PetWindow` 的窗口大小（保持 64x64）
- ❌ 农历用 `zhdate`（不是 `lunardate`）

---

## Phase 1: 扩展状态 + 水獭外观

**文件:** `pet/states.py`, `pet/animator.py`

### T1.1: 更新 `pet/states.py`

在 `PetState` 枚举中添加 4 个新状态：
```python
EAT = "eat"       # 吃鱼
PLAY = "play"     # 玩石头
GROOM = "groom"   # 梳理毛发
REST = "rest"     # 晒太阳休息
```

扩展 `TRANSITIONS` 字典（9 个状态全量）：
```python
PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY, PetState.ALERT, PetState.EAT, PetState.PLAY, PetState.GROOM, PetState.REST],
PetState.WALK:  [PetState.IDLE, PetState.HAPPY, PetState.ALERT, PetState.EAT],
PetState.SLEEP: [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
PetState.HAPPY: [PetState.IDLE, PetState.ALERT],
PetState.ALERT: [PetState.IDLE],
PetState.EAT:   [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
PetState.PLAY:  [PetState.IDLE, PetState.WALK, PetState.HAPPY, PetState.ALERT],
PetState.GROOM: [PetState.IDLE, PetState.WALK, PetState.ALERT],
PetState.REST:  [PetState.IDLE, PetState.SLEEP, PetState.HAPPY, PetState.ALERT],
```

扩展 `FRAME_INTERVALS`：
```python
PetState.EAT: 350,
PetState.PLAY: 250,
PetState.GROOM: 400,
PetState.REST: 600,
```

### T1.2: 重写 `pet/animator.py` — 水獭外观

重写 `generate_placeholder_frame()` 中所有 9 个状态的绘制逻辑。

**水獭基础身体（所有状态共享）：**
- 流线型身体：椭圆 (8,10,16,16)，深棕色 `QColor(92, 58, 30)`
- 浅色腹部：下半椭圆叠加，浅米色 `QColor(212, 167, 106)`
- 短圆耳朵：头顶两个 3x3 小圆
- 黑色眼睛：2x2 小圆 + 1x1 白色高光
- 长扁尾巴：从身体底部向后延伸的弧线

**各状态差异（关键视觉区分）：**
- **IDLE**: 坐姿，前爪自然垂下，尾巴贴地
- **WALK**: 身体倾斜 1px，四肢交替伸出（帧动画），尾巴翘起
- **SLEEP**: 蜷缩成小球（椭圆更小更圆），闭眼（横线），"z" 字浮动
- **HAPPY**: 身体弹跳（帧间上下 1px），眯眼（笑弧），嘴巴张开（红色小弧）
- **ALERT**: 左右抖动（帧间 ±1px），大眼睛（3x3），头顶红色 "!" 
- **EAT**: 前爪抱鱼（小鱼形状），嘴巴张合（帧动画），鱼逐渐变小
- **PLAY**: 仰躺（身体横放），爪子拨弄小石头（帧间左右移动）
- **GROOM**: 坐姿，前爪抬到嘴边，舌头伸出（粉色小线）
- **REST**: 趴着（扁椭圆），半闭眼（小点），角落画太阳光线

### T1.3: 添加 `state_changed` 信号

在 `SpriteAnimator` 类中：
```python
from PySide6.QtCore import Signal
class SpriteAnimator(QObject):
    state_changed = Signal(PetState)
```

在 `set_state()` 方法成功切换后 emit：
```python
self.state_changed.emit(state)
```

### T1.4: 更新 `generate_all_placeholder_frames()`

帧数：`{IDLE:4, WALK:6, SLEEP:4, HAPPY:4, ALERT:4, EAT:6, PLAY:6, GROOM:4, REST:4}`

### 验证
- `python main.py` — 目视确认 9 个状态外观明显不同
- `python -m pytest tests/` — 无回归
- 检查 state_changed 信号是否正常 emit

---

## Phase 2: 屏幕移动 + 行为调度扩展

**文件:** `pet/movement.py` (新建), `pet/behavior.py`, `main.py`

### T2.1: 新建 `pet/movement.py`

```python
from PySide6.QtCore import QObject, QTimer, QPoint
from PySide6.QtGui import QTransform
import random
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
        self._facing_right = True
        self._moving = False

        animator.state_changed.connect(self._on_state_changed)

    def _on_state_changed(self, state: PetState):
        if state == PetState.WALK:
            self._pick_destination()
            self._timer.start(50)
            self._moving = True
        else:
            self._timer.stop()
            self._moving = False

    def _pick_destination(self):
        screen = self._window.screen()
        if screen:
            geo = screen.availableGeometry()
            x = random.randint(geo.left(), geo.right() - 64)
            y = random.randint(geo.top(), geo.bottom() - 64)
            self._target = QPoint(x, y)

    def _move_step(self):
        if not self._target:
            return
        pos = self._window.pos()
        dx = self._target.x() - pos.x()
        dy = self._target.y() - pos.y()
        dist = (dx**2 + dy**2) ** 0.5

        if dist < 5:
            self._pick_destination()
            return

        step = 3
        nx = pos.x() + int(step * dx / dist)
        ny = pos.y() + int(step * dy / dist)

        # 朝向
        if dx > 0 and not self._facing_right:
            self._facing_right = True
        elif dx < 0 and self._facing_right:
            self._facing_right = False

        self._window.move_to(nx, ny)

    def stop(self):
        self._timer.stop()
        self._moving = False

    @property
    def facing_right(self) -> bool:
        return self._facing_right
```

### T2.2: 更新 `pet/behavior.py` — 9 状态随机调度

修改 `_on_random_switch()` 方法，从 IDLE 随机切换到多个状态：

```python
# 权重表
_BEHAVIOR_WEIGHTS = {
    PetState.WALK: 30,
    PetState.EAT: 20,
    PetState.PLAY: 15,
    PetState.GROOM: 15,
    PetState.REST: 20,
}

# 各状态持续时间范围（毫秒）
_BEHAVIOR_DURATIONS = {
    PetState.EAT: (5000, 8000),
    PetState.PLAY: (8000, 15000),
    PetState.GROOM: (4000, 7000),
    PetState.REST: (10000, 20000),
    PetState.WALK: (5000, 10000),
}

def _on_random_switch(self):
    if self._animator.current_state != PetState.IDLE:
        return
    states = list(self._BEHAVIOR_WEIGHTS.keys())
    weights = list(self._BEHAVIOR_WEIGHTS.values())
    chosen = random.choices(states, weights=weights, k=1)[0]
    self._animator.set_state(chosen)
    lo, hi = self._BEHAVIOR_DURATIONS[chosen]
    duration = random.randint(lo, hi)
    QTimer.singleShot(duration, self._on_behavior_done)

def _on_behavior_done(self):
    if self._animator.current_state != PetState.IDLE:
        self._animator.set_state(PetState.IDLE)
    self._schedule_random_switch()
```

### T2.3: 集成到 `main.py`

在 `main()` 函数中 animator.start() 之后添加：
```python
from pet.movement import MovementController
movement = MovementController(window, animator)
```

用户拖拽时停止自主移动（在 `mouseReleaseEvent` 或 position_changed 处理中）：
```python
def _on_position_changed(x, y):
    if movement._moving:
        movement.stop()
    # ... existing save logic
```

退出时停止：
```python
app.aboutToQuit.connect(movement.stop)
```

### 验证
- `python main.py` — 观察 WALK 时水獭满屏走动
- 拖拽后水獭应停止自主移动
- 各状态自动轮换正常

---

## Phase 3: 状态头标 + 过渡动画

**文件:** `pet/indicator.py` (新建), `pet/transition.py` (新建), `main.py`

### T3.1: 新建 `pet/indicator.py`

参考 `pet/bubble.py` 的窗口模式（FramelessWindowHint + WindowStaysOnTopHint + Tool）。

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor, QFont
from pet.states import PetState

class StateIndicator(QWidget):
    """悬浮在宠物头顶的状态 emoji 指示器。"""

    STATE_EMOJI = {
        PetState.WALK: "👣",
        PetState.SLEEP: "💤",
        PetState.HAPPY: "❤️",
        PetState.ALERT: "🔔",
        PetState.EAT: "🐟",
        PetState.PLAY: "⚽",
        PetState.GROOM: "✨",
        PetState.REST: "☀️",
    }

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFixedSize(QSize(24, 24))
        self._emoji = ""
        self._float_offset = 0
        self._float_timer = QTimer()
        self._float_timer.timeout.connect(self._animate_float)
        self._float_timer.start(500)

    def show_for_state(self, state: PetState, anchor_x: int, anchor_y: int):
        self._emoji = self.STATE_EMOJI.get(state, "")
        if not self._emoji:
            self.hide()
            return
        x = anchor_x + 32 - 12  # 居中于 64px 窗口
        y = anchor_y - 28 - self._float_offset
        self.move(x, y)
        self.show()
        self.update()

    def update_position(self, anchor_x: int, anchor_y: int):
        if self.isVisible():
            x = anchor_x + 32 - 12
            y = anchor_y - 28 - self._float_offset
            self.move(x, y)

    def _animate_float(self):
        self._float_offset = 2 if self._float_offset == 0 else 0
        if self.isVisible():
            pos = self.pos()
            self.move(pos.x(), pos.y() + (2 if self._float_offset else -2))

    def paintEvent(self, event):
        if not self._emoji:
            return
        painter = QPainter(self)
        font = QFont("Segoe UI Emoji", 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._emoji)
        painter.end()
```

### T3.2: 新建 `pet/transition.py`

```python
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter
from pet.states import PetState

class TransitionAnimator(QObject):
    """状态切换的 300ms alpha 渐变过渡。"""

    frame_ready = Signal(QPixmap)
    transition_complete = Signal()

    def __init__(self):
        super().__init__()
        self._from_pixmap = None
        self._to_pixmap = None
        self._alpha = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._step)
        self._active = False

    def start_transition(self, from_pixmap: QPixmap, to_pixmap: QPixmap, duration_ms=300):
        self._from_pixmap = from_pixmap
        self._to_pixmap = to_pixmap
        self._alpha = 0.0
        self._step_size = 1.0 / (duration_ms / 30)
        self._active = True
        self._timer.start(30)

    def interrupt(self):
        """ALERT 可中断过渡。"""
        self._timer.stop()
        self._active = False

    def _step(self):
        self._alpha = min(1.0, self._alpha + self._step_size)
        blended = self._blend(self._from_pixmap, self._to_pixmap, self._alpha)
        self.frame_ready.emit(blended)
        if self._alpha >= 1.0:
            self._timer.stop()
            self._active = False
            self.transition_complete.emit()

    def _blend(self, from_pm: QPixmap, to_pm: QPixmap, alpha: float) -> QPixmap:
        result = QPixmap(from_pm.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setOpacity(1.0 - alpha)
        painter.drawPixmap(0, 0, from_pm)
        painter.setOpacity(alpha)
        painter.drawPixmap(0, 0, to_pm)
        painter.end()
        return result

    @property
    def is_active(self) -> bool:
        return self._active
```

### T3.3: 集成到 `main.py`

```python
from pet.indicator import StateIndicator
from pet.transition import TransitionAnimator

indicator = StateIndicator()
transition = TransitionAnimator()

# 状态变化 → 头标
def on_state_changed(state):
    pos = window.get_position()
    indicator.show_for_state(state, pos[0], pos[1])
animator.state_changed.connect(on_state_changed)

# 位置变化 → 头标跟随
def on_pos_changed(x, y):
    indicator.update_position(x, y)
window.position_changed.connect(on_pos_changed)

# 过渡动画集成到 update_display
def update_display():
    pixmap = animator.current_pixmap()
    if pixmap:
        if transition.is_active:
            # 过渡中使用过渡帧（通过 frame_ready 信号）
            pass
        else:
            window.set_pixmap(pixmap)

transition.frame_ready.connect(lambda pm: window.set_pixmap(pm))
```

### 验证
- `python main.py` — 状态切换时头顶出现对应 emoji
- 拖拽宠物时 emoji 跟随
- 状态切换有 alpha 渐变效果

---

## Phase 4: 节日换装系统

**文件:** `pet/holiday_engine.py` (新建), `pet/costume.py` (新建), `data/holidays.json` (新建), `data/costumes.json` (新建), `data/settings.py`, `main.py`

### T4.1: 安装依赖
```bash
pip install zhdate
```

### T4.2: 新建 `data/holidays.json`

```json
{
  "holidays": [
    {"id": "spring_festival", "name": "春节", "type": "lunar", "month": 1, "day": 1, "duration_days": 3, "costume": "red_lantern_hat", "emoji": "🧧"},
    {"id": "mid_autumn", "name": "中秋节", "type": "lunar", "month": 8, "day": 15, "duration_days": 1, "costume": "moon_cake_hat", "emoji": "🥮"},
    {"id": "dragon_boat", "name": "端午节", "type": "lunar", "month": 5, "day": 5, "duration_days": 1, "costume": "dragon_hat", "emoji": "🐉"},
    {"id": "national_day", "name": "国庆节", "type": "solar", "month": 10, "day": 1, "duration_days": 3, "costume": "flag_ribbon", "emoji": "🇨🇳"},
    {"id": "new_year", "name": "元旦", "type": "solar", "month": 1, "day": 1, "duration_days": 1, "costume": "party_hat", "emoji": "🎉"},
    {"id": "children_day", "name": "儿童节", "type": "solar", "month": 6, "day": 1, "duration_days": 1, "costume": "balloon_hat", "emoji": "🎈"}
  ]
}
```

### T4.3: 新建 `data/costumes.json`

每个服装是一组 QPainter 绘制指令（在 32x32 精灵上叠加）：

```json
{
  "red_lantern_hat": {
    "type": "hat",
    "anchor_y": 0,
    "commands": [
      {"shape": "ellipse", "x": 10, "y": 0, "w": 12, "h": 10, "fill": [220, 20, 20]},
      {"shape": "rect", "x": 14, "y": -3, "w": 4, "h": 4, "fill": [255, 215, 0]},
      {"shape": "line", "x1": 16, "y1": -3, "x2": 16, "y2": -7, "pen": [139, 69, 19, 2]}
    ]
  },
  "moon_cake_hat": {
    "type": "hat",
    "anchor_y": 2,
    "commands": [
      {"shape": "ellipse", "x": 10, "y": 2, "w": 12, "h": 8, "fill": [210, 160, 60]},
      {"shape": "text", "x": 12, "y": 6, "text": "月", "color": [139, 69, 19]}
    ]
  },
  "dragon_hat": {
    "type": "hat",
    "anchor_y": 0,
    "commands": [
      {"shape": "ellipse", "x": 8, "y": 0, "w": 16, "h": 8, "fill": [50, 180, 50]},
      {"shape": "ellipse", "x": 12, "y": 2, "w": 3, "h": 3, "fill": [255, 255, 0]},
      {"shape": "ellipse", "x": 17, "y": 2, "w": 3, "h": 3, "fill": [255, 255, 0]}
    ]
  },
  "flag_ribbon": {
    "type": "ribbon",
    "anchor_y": 10,
    "commands": [
      {"shape": "rect", "x": 2, "y": 10, "w": 28, "h": 4, "fill": [220, 20, 20]},
      {"shape": "ellipse", "x": 4, "y": 10, "w": 4, "h": 4, "fill": [255, 215, 0]}
    ]
  },
  "party_hat": {
    "type": "hat",
    "anchor_y": 0,
    "commands": [
      {"shape": "polygon", "points": [[16,0],[8,12],[24,12]], "fill": [100, 200, 255]},
      {"shape": "ellipse", "x": 14, "y": -2, "w": 4, "h": 4, "fill": [255, 215, 0]}
    ]
  },
  "balloon_hat": {
    "type": "hat",
    "anchor_y": -4,
    "commands": [
      {"shape": "ellipse", "x": 11, "y": -8, "w": 10, "h": 12, "fill": [255, 100, 100]},
      {"shape": "line", "x1": 16, "y1": 4, "x2": 16, "y2": 10, "pen": [100, 100, 100, 1]}
    ]
  }
}
```

### T4.4: 新建 `pet/holiday_engine.py`

```python
import json
from datetime import date, timedelta
from PySide6.QtCore import QObject, QTimer, Signal
from zhdate import ZhDate

class HolidayEngine(QObject):
    holiday_active = Signal(str, str, str)  # holiday_id, costume_id, emoji
    holiday_ended = Signal()

    def __init__(self, holidays_path: str):
        super().__init__()
        with open(holidays_path, "r", encoding="utf-8") as f:
            self._holidays = json.load(f)["holidays"]
        self._active_holiday = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._check)
        self._timer.start(3600 * 1000)  # 每小时检查
        self._check()

    def _check(self):
        today = date.today()
        for h in self._holidays:
            if self._is_in_window(today, h):
                if self._active_holiday != h["id"]:
                    self._active_holiday = h["id"]
                    self.holiday_active.emit(h["id"], h["costume"], h["emoji"])
                return
        if self._active_holiday:
            self._active_holiday = None
            self.holiday_ended.emit()

    def _is_in_window(self, today: date, holiday: dict) -> bool:
        if holiday["type"] == "solar":
            h_date = date(today.year, holiday["month"], holiday["day"])
        else:
            try:
                zh = ZhDate(today.year, holiday["month"], holiday["day"])
                h_date = zh.to_datetime().date()
            except Exception:
                return False
        delta = (today - h_date).days
        return 0 <= delta < holiday["duration_days"]

    def stop(self):
        self._timer.stop()
```

### T4.5: 新建 `pet/costume.py`

```python
import json
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPolygon
from PySide6.QtCore import QPoint

class CostumeRenderer:
    def __init__(self):
        self._costumes = {}
        self._active = None

    def load_costumes(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self._costumes = json.load(f)

    def set_active_costume(self, costume_id: str):
        self._active = costume_id

    def clear_costume(self):
        self._active = None

    def has_active_costume(self) -> bool:
        return self._active is not None

    def apply_costume(self, base_pixmap: QPixmap) -> QPixmap:
        if not self._active or self._active not in self._costumes:
            return base_pixmap
        result = base_pixmap.copy()
        painter = QPainter(result)
        costume = self._costumes[self._active]
        for cmd in costume["commands"]:
            self._execute_command(painter, cmd)
        painter.end()
        return result

    def _execute_command(self, painter: QPainter, cmd: dict):
        shape = cmd["shape"]
        if "fill" in cmd:
            painter.setBrush(QBrush(QColor(*cmd["fill"])))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
        if "pen" in cmd:
            r, g, b, w = cmd["pen"]
            painter.setPen(QPen(QColor(r, g, b), w))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        if shape == "ellipse":
            painter.drawEllipse(cmd["x"], cmd["y"], cmd["w"], cmd["h"])
        elif shape == "rect":
            painter.drawRect(cmd["x"], cmd["y"], cmd["w"], cmd["h"])
        elif shape == "line":
            painter.drawLine(cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"])
        elif shape == "text":
            painter.setPen(QPen(QColor(*cmd["color"])))
            painter.drawText(cmd["x"], cmd["y"], cmd["text"])
```

### T4.6: 更新 `data/settings.py`

添加 `costume_enabled: bool = True`，schema 版本升到 2。

### T4.7: 集成到 `main.py`

```python
from pet.holiday_engine import HolidayEngine
from pet.costume import CostumeRenderer

holiday_engine = HolidayEngine(str(get_asset_path("data/holidays.json")))
costume_renderer = CostumeRenderer()
costume_renderer.load_costumes(str(get_asset_path("data/costumes.json")))

def on_holiday_active(holiday_id, costume_id, emoji):
    costume_renderer.set_active_costume(costume_id)
    pos = window.get_position()
    bubble.show_message(f"{emoji} 节日快乐！", pos[0] + 32, pos[1], duration_ms=5000)

def on_holiday_ended():
    costume_renderer.clear_costume()

holiday_engine.holiday_active.connect(on_holiday_active)
holiday_engine.holiday_ended.connect(on_holiday_ended)

# 修改 update_display
def update_display():
    pixmap = animator.current_pixmap()
    if pixmap:
        if costume_renderer.has_active_costume():
            pixmap = costume_renderer.apply_costume(pixmap)
        window.set_pixmap(pixmap)

# 退出时
app.aboutToQuit.connect(holiday_engine.stop)
```

### 验证
- `pip install zhdate` 成功
- 修改系统日期到春节 → 水獭戴红灯笼帽 + 显示 🧧
- 修改系统日期到非节日 → 服装消失
- `python -m pytest tests/` 无回归

---

## Phase 5: 最终验证

1. `python main.py` — 完整功能验证
2. `python -m pytest tests/` — 全量测试
3. 检查所有新文件的 import 无循环依赖
4. 确认 `generate_all_placeholder_frames()` 包含所有 9 个状态
5. 确认 `TRANSITIONS` 表无遗漏（每个状态都能回 IDLE）
6. 确认 ALERT 可中断任何状态和过渡
7. 确认拖拽时 MovementController 停止

---

## 文件清单

| Phase | 文件 | 操作 |
|---|---|---|
| 1 | `pet/states.py` | 修改 |
| 1 | `pet/animator.py` | 修改 |
| 2 | `pet/movement.py` | 新建 |
| 2 | `pet/behavior.py` | 修改 |
| 2 | `main.py` | 修改 |
| 3 | `pet/indicator.py` | 新建 |
| 3 | `pet/transition.py` | 新建 |
| 3 | `main.py` | 修改 |
| 4 | `data/holidays.json` | 新建 |
| 4 | `data/costumes.json` | 新建 |
| 4 | `pet/holiday_engine.py` | 新建 |
| 4 | `pet/costume.py` | 新建 |
| 4 | `data/settings.py` | 修改 |
| 4 | `main.py` | 修改 |
