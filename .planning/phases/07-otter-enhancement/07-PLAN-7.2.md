# Plan 7.2 — 屏幕移动 + 行为调度扩展

**Wave:** 1 (依赖 7.1 的新状态和信号)
**Requirements:** OTTER-02

## Goal
WALK 状态水獭真正满屏幕走动，新增行为调度支持所有 9 个状态的自主切换。

## Tasks

### T1: 新建 `pet/movement.py` — MovementController
```python
class MovementController(QObject):
    """控制 WALK 状态的屏幕自主移动。"""

    def __init__(self, window: PetWindow, animator: SpriteAnimator):
        # 连接 animator.state_changed
        # movement_timer = QTimer(50ms)
        # _facing_right: bool
        # _target_pos: QPoint
        # _moving_autonomously: bool

    def _on_state_changed(self, state: PetState):
        # WALK → 开始移动
        # 非 WALK → 停止移动

    def _pick_destination(self):
        # 获取屏幕可用区域
        # 随机选目标点（避开当前位置附近）

    def _move_step(self):
        # 计算方向向量
        # 步进 2-3px
        # 到达阈值内 → 选新目标或回 IDLE
        # 翻转精灵（QTransform.mirror）

    def stop(self):
        # 停止移动定时器
```

### T2: 更新 `pet/behavior.py` — 新行为调度
- 修改 `_on_random_switch()` 支持从 IDLE 随机切换到所有活动状态
- 权重分配：WALK 30%, EAT 20%, PLAY 15%, GROOM 15%, REST 20%
- 各状态持续时间：EAT 5-8s, PLAY 8-15s, GROOM 4-7s, REST 10-20s
- 添加 `walk_started` / `walk_ended` 信号

### T3: 集成到 `main.py`
- 创建 MovementController(window, animator)
- 连接 behavior.walk_started → movement.start
- 连接 behavior.walk_ended → movement.stop
- 用户拖拽时 movement.stop()

## 验证
```bash
python main.py  # 观察水獭满屏幕走动
# 手动拖拽后水獭应停止自主移动
# 等待状态自动切换
```

## 交付物
- [x] `pet/movement.py` — MovementController
- [x] `pet/behavior.py` — 9 状态行为调度
- [x] `main.py` — 移动集成
