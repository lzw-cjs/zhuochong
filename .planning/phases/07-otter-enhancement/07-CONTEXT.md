# Phase 7 Context — 水獭宠物功能扩展

## 来源
用户反馈（2026-05-11）：v1.0 完成后发现以下问题

## 问题陈述

### P1: 外观不清晰
- 当前占位图是棕色椭圆（QPainter 代码绘制），注释写的是"树懒"而非水獭
- 用户看不出是水獭，各状态视觉差异太小

### P2: WALK 不移动
- WALK 状态只在原地摆动手爪，窗口位置不变
- 用户期望水獭满屏幕走动

### P3: 状态不可见
- 没有头标指示器，用户无法一眼看出当前状态
- 需要每个状态有对应的 emoji/图标悬浮显示

### P4: 切换生硬
- 状态切换是瞬间跳变（frame 0 直接替换），没有过渡动画

### P5: 缺少节日换装
- 用户期望节日期间水獭自动换装（春节、中秋、端午等）

## 需求清单

| ID | 需求 | 优先级 |
|---|---|---|
| OTTER-01 | 新增 4 个状态：EAT/PLAY/GROOM/REST | P0 |
| OTTER-02 | WALK 状态屏幕真正移动 | P0 |
| OTTER-03 | 状态头标指示器（emoji 悬浮） | P0 |
| OTTER-04 | 状态过渡动画（300ms alpha 渐变） | P1 |
| OTTER-05 | 节日换装系统（自动检测+QPainter 叠加） | P1 |
| OTTER-06 | 改善水獭外观（流线型身体、短耳、蹼足、长尾） | P0 |

## 约束
- 保持 32x32 像素风（缩放到 64x64 窗口）
- 所有绘制通过 QPainter（暂不需要外部精灵图文件）
- 遵循现有模式：JsonStore、QTimer 轮询、Signal/Slot
- 农历用 `lunardate` 包转换

## 涉及文件

### 修改
- `pet/states.py` — 新状态枚举 + 转换表
- `pet/animator.py` — 帧生成 + 过渡动画 + 水獭外观
- `pet/behavior.py` — 新行为调度
- `pet/window.py` — 移动集成
- `main.py` — 全部集成

### 新建
- `pet/movement.py` — 屏幕移动控制器
- `pet/indicator.py` — 状态头标指示器
- `pet/transition.py` — 过渡动画器
- `pet/holiday_engine.py` — 节日检测引擎
- `pet/costume.py` — 换装渲染器
- `data/holidays.json` — 节日数据
- `data/costumes.json` — 服装数据
