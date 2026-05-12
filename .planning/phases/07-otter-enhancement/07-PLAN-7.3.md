# Plan 7.3 — 状态头标指示器 + 过渡动画

**Wave:** 2 (依赖 7.1 的 state_changed 信号)
**Requirements:** OTTER-03, OTTER-04

## Goal
每个状态显示对应的 emoji 头标，状态切换有 300ms alpha 渐变过渡。

## Tasks

### T1: 新建 `pet/indicator.py` — StateIndicator
```python
class StateIndicator(QWidget):
    """悬浮在宠物头顶的状态指示器。"""

    STATE_EMOJI = {
        PetState.IDLE: "",        # 无指示器
        PetState.WALK: "👣",
        PetState.SLEEP: "💤",
        PetState.HAPPY: "❤️",
        PetState.ALERT: "🔔",
        PetState.EAT: "🐟",
        PetState.PLAY: "⚽",
        PetState.GROOM: "✨",
        PetState.REST: "☀️",
    }

    def show_for_state(self, state: PetState, anchor_x: int, anchor_y: int):
        # IDLE → hide()
        # 其他 → 显示 emoji，定位在 anchor 上方

    def update_position(self, anchor_x: int, anchor_y: int):
        # 跟随宠物位置

    def _animate_float(self):
        # QTimer 上下浮动 1-2px
```

### T2: 新建 `pet/transition.py` — TransitionAnimator
```python
class TransitionAnimator(QObject):
    """状态切换的 alpha 渐变过渡。"""

    frame_ready = Signal(QPixmap)

    def start_transition(self, from_pixmap: QPixmap, to_state: PetState, duration_ms=300):
        # 保存旧帧
        # 生成新状态首帧
        # 启动 QTimer (30ms 步进)

    def _blend_step(self):
        # QPainter.setOpacity(alpha) 混合两帧
        # alpha 从 0→1 线性插值
        # 完成后 emit transition_complete

    def interrupt(self):
        # ALERT 可中断过渡
```

### T3: 集成到 `main.py`
- 创建 StateIndicator()
- 连接 animator.state_changed → indicator.show_for_state
- 连接 window.position_changed → indicator.update_position
- 在 update_display() 中集成过渡动画

## 验证
```bash
python main.py
# 观察状态切换时的 emoji 头标变化
# 观察过渡动画（alpha 渐变）
# 拖拽宠物时头标跟随
```

## 交付物
- [x] `pet/indicator.py` — StateIndicator
- [x] `pet/transition.py` — TransitionAnimator
- [x] `main.py` — 集成
