# Phase 7 Summary — 水獭宠物功能扩展

## Status: Planned

## Plans

| Plan | Name | Wave | Status |
| --- | --- | --- | --- |
| P7.1 | 扩展状态 + 水獭外观 | 0 | Pending |
| P7.2 | 屏幕移动 + 行为调度 | 1 | Pending |
| P7.3 | 状态头标 + 过渡动画 | 2 | Pending |
| P7.4 | 节日换装系统 | 3 | Pending |

## Wave Dependencies

```
Wave 0: P7.1 (基础层 — 新状态 + 外观 + state_changed 信号)
Wave 1: P7.2 (依赖 P7.1 的新状态和信号)
Wave 2: P7.3 (依赖 P7.1 的 state_changed 信号)
Wave 3: P7.4 (依赖 P7.1 的 animator, 独立于 7.2/7.3)
```

## New Files

| File | Purpose |
|---|---|
| `pet/movement.py` | WALK 屏幕移动控制器 |
| `pet/indicator.py` | 状态 emoji 头标指示器 |
| `pet/transition.py` | 状态过渡 alpha 渐变 |
| `pet/holiday_engine.py` | 节日检测引擎（含农历） |
| `pet/costume.py` | QPainter 服装叠加渲染器 |
| `data/holidays.json` | 节日定义数据 |
| `data/costumes.json` | 服装绘制命令数据 |

## Modified Files

| File | Changes |
|---|---|
| `pet/states.py` | +4 状态枚举、转换表、帧间隔 |
| `pet/animator.py` | 水獭外观重绘、state_changed 信号、新状态帧 |
| `pet/behavior.py` | 9 状态随机调度、权重分配 |
| `pet/window.py` | 移动集成（拖拽暂停自主移动） |
| `data/settings.py` | +costume_enabled 字段，schema v2 |
| `main.py` | 全部新模块集成 |

## Dependencies

| Package | Purpose |
|---|---|
| lunardate | 农历转公历（节日系统） |
