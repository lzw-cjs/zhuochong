# Plan 7.1 — 扩展状态系统 + 改善水獭外观

**Wave:** 0 (基础层，无依赖)
**Requirements:** OTTER-01, OTTER-06

## Goal
新增 4 个状态（EAT/PLAY/GROOM/REST），重写占位图绘制使其更像水獭，添加 state_changed 信号。

## Tasks

### T1: 更新 `pet/states.py`
- 新增 PetState 枚举：EAT, PLAY, GROOM, REST
- 扩展 TRANSITIONS 转换表（9 个状态全量）
- 扩展 FRAME_INTERVALS（EAT:350, PLAY:250, GROOM:400, REST:600）

### T2: 重写 `pet/animator.py` — 水獭外观
重写 `generate_placeholder_frame()` 中所有状态的绘制逻辑：

**水獭特征绘制：**
- 流线型身体（椭圆，深棕色 #5C3A1E）
- 浅色腹部（下半椭圆，浅米色 #D4A76A）
- 短圆耳朵（头顶两个小圆）
- 黑色小圆眼 + 白色高光
- 蹼状脚掌（扇形线条）
- 长扁尾巴（弧线）

**各状态差异：**
- IDLE：坐姿，前爪举起，尾巴垂地
- WALK：身体倾斜，四肢交替，尾巴翘起
- SLEEP：蜷缩成球，闭眼（横线），Z 字浮动
- HAPPY：身体弹跳，眯眼（笑弧），嘴巴张开
- ALERT：抖动，大眼睛，红色感叹号
- EAT：前爪抱鱼，嘴巴张合，鱼逐渐变小
- PLAY：仰躺，爪子拨弄石头，石头左右滚动
- GROOM：坐姿，前爪抬到嘴边，舔毛动作
- REST：趴着，半闭眼，角落太阳光线

### T3: 添加 state_changed 信号
- 在 SpriteAnimator 中添加 `state_changed = Signal(PetState)`
- 在 `set_state()` 成功后 emit

### T4: 更新 `generate_all_placeholder_frames()`
- 为 4 个新状态生成帧序列
- 帧数：EAT=6, PLAY=6, GROOM=4, REST=4

## 验证
```bash
python main.py  # 目视检查 9 个状态的外观差异
python -m pytest tests/  # 无回归
```

## 交付物
- [x] `pet/states.py` — 9 个状态枚举 + 完整转换表
- [x] `pet/animator.py` — 水獭外观占位图 + state_changed 信号
