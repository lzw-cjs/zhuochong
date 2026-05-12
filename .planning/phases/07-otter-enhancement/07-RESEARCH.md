# Phase 7 Research — 水獭宠物功能扩展

## 水獭行为习性（用于状态设计）

| 行为 | 描述 | 对应状态 |
|---|---|---|
| 觅食捕鱼 | 每天吃体重 15-25% 的鱼 | EAT |
| 玩石头 | 水獭著名习性，仰躺用爪子转石头 | PLAY |
| 梳理毛发 | 非常注重毛发护理，用干草/树叶擦拭 | GROOM |
| 晒太阳 | 中午在岸上休息、晒太阳 | REST |
| 爬行/游泳 | 清晨和黄昏活跃 | WALK |
| 蜷缩睡觉 | 夜间或休息时蜷缩 | SLEEP |

## 现有架构分析

### 渲染管线
```
50ms QTimer → animator.current_pixmap() → window.set_pixmap()
```
- 20 FPS 刷新率
- 32x32 QPainter 占位图 → FastTransformation 缩放到 64x64
- 无自主移动（WALK 只是原地摆动）

### 状态机
```
BehaviorScheduler (QTimer) → animator.set_state() → SpriteAnimator
```
- BehaviorScheduler 无 window 引用
- set_state() 瞬间切换，无过渡
- 状态改变无信号通知外部

### 位置管理
```
window.position_changed → Settings.save() (500ms debounce)
```
- 仅用户拖拽触发
- 启动时恢复位置

## 关键技术点

### 屏幕移动实现
- 需要给 BehaviorScheduler 添加 window 引用或新建 MovementController
- 移动步进 2-3px/tick，50ms 间隔
- 到达目标点后选新目标或回 IDLE
- 需要跟踪朝向（QTransform.mirror 翻转精灵）

### 头标指示器
- 参考 ChatBubble 模式：独立 frameless+transparent+always-on-top widget
- 定位在宠物窗口上方居中
- 需要跟随宠物位置（连接 position_changed）

### 过渡动画
- 在 SpriteAnimator 中添加 alpha 渐变
- 300ms 总时长，30ms 步进（10 步）
- ALERT 可中断任何过渡

### 农历转换
- `lunardate` 包：lunar-to-gregorian 转换
- 需处理闰月情况
- 每日检查一次（1 小时 QTimer）

## 依赖

| 包 | 用途 | 是否必须 |
|---|---|---|
| lunardate | 农历转公历 | 是（节日系统） |
| PySide6 | GUI 框架 | 已有 |
