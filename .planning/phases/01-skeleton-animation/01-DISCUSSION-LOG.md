# Phase 1: Skeleton & Animation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-09
**Phase:** 1-Skeleton & Animation
**Areas discussed:** Sprite 素材设计, 窗口行为细节, 数据存储结构, 宠物行为模式

---

## Sprite 素材设计

### Sprite 尺寸

| Option | Description | Selected |
|--------|-------------|----------|
| 32x32 像素 | 经典像素风，非常小巧，适合小屏幕 | ✓ |
| 48x48 像素 | 稍大，细节更丰富，适合高分屏 | |
| 64x64 像素 | 较大，动画表现力强，但占屏幕空间多 | |

**User's choice:** 32x32 像素
**Notes:** 选择经典像素风格

### 动物类型

| Option | Description | Selected |
|--------|-------------|----------|
| 小猫咪 | 经典桌面宠物，可爱治愈 | |
| 小狗 | 活泼好动，适合动画表现 | |
| 小龙/龙崽 | 神秘感，像素风很搭 | |
| 其他动物 | 用户自选 | ✓ |

**User's choice:** 树懒 (sloth)
**Notes:** 用户选择树懒——慢悠悠的性格很适合桌面陪伴

### 素材来源

| Option | Description | Selected |
|--------|-------------|----------|
| 使用现有素材 | 用户提供或指定一个现有的像素风树懒素材包 | |
| 先用占位素材 | 我生成简单的占位 Sprite，后续替换为正式素材 | ✓ |
| 代码生成占位图 | 用代码绘制简单几何形状作为临时素材 | |

**User's choice:** 先用占位素材
**Notes:** 先确保动画引擎正常工作，后续替换正式素材

### 动画状态

| Option | Description | Selected |
|--------|-------------|----------|
| idle（挂在树枝上） | 挂在树枝上慢慢晃，最基本的待机动作 | ✓ |
| walk（缓慢爬行） | 慢慢爬行，用于拖拽后的移动动画 | ✓ |
| sleep（蜷缩睡觉） | 蜷成一团睡觉，屏幕保护时触发 | ✓ |
| happy（开心摇晃） | 开心摇晃，点击反馈时触发 | ✓ |

**User's choice:** 全部选择
**Notes:** 4 个动画状态全部纳入 Phase 1

---

## 窗口行为细节

### 任务栏显示

| Option | Description | Selected |
|--------|-------------|----------|
| 不显示在任务栏 | 宠物不在任务栏显示，更像真正的桌面伴侣 | ✓ |
| 显示在任务栏 | 宠物在任务栏有独立窗口条目 | |

**User's choice:** 不显示在任务栏
**Notes:** 使用 Qt.Tool 标志实现

### 层级行为

| Option | Description | Selected |
|--------|-------------|----------|
| 始终置顶 | 宠物始终在最上层，不会被其他窗口遮挡 | |
| 智能置顶（全屏时隐藏） | 正常使用时置顶，但全屏应用（游戏/视频）时自动隐藏 | ✓ |

**User's choice:** 智能置顶（全屏时隐藏）
**Notes:** 需要实现全屏应用检测逻辑

### 多显示器

| Option | Description | Selected |
|--------|-------------|----------|
| 自由跨屏 | 宠物可以在任意显示器上，拖拽不受限制 | ✓ |
| 仅主显示器 | 宠物只在主显示器上活动 | |

**User's choice:** 自由跨屏
**Notes:** 无限制

---

## 数据存储结构

### 存储位置

| Option | Description | Selected |
|--------|-------------|----------|
| AppData 目录 | %APPDATA%/SmartDesktopPet/，Windows 标准做法 | ✓ |
| 应用目录下 | 应用同级目录 data/，便于便携使用 | |
| 文档目录 | 用户文档目录下 | |

**User's choice:** AppData 目录
**Notes:** Windows 标准做法

### 持久化设置

| Option | Description | Selected |
|--------|-------------|----------|
| 宠物位置 | 宠物在屏幕上的 X/Y 坐标 | ✓ |
| 宠物状态 | 当前动画状态、心情值等 | ✓ |
| 基础偏好 | 音量、是否静音、启动时是否自动运行 | ✓ |
| 日历配置 | 日历颜色、优先级标签等 | ✓ |

**User's choice:** 全部选择
**Notes:** Phase 1 先建立数据结构，日历相关字段可为空

---

## 宠物行为模式

### 自主行为

| Option | Description | Selected |
|--------|-------------|----------|
| 纯被动（不动） | 宠物静止不动，只有用户交互时才响应 | |
| 原地切换状态 | 宠物偶尔自己切换动画状态，但不移动位置 | ✓ |
| 原地+偶尔爬行 | 宠物会在屏幕边缘缓慢爬行 | |

**User's choice:** 原地切换状态
**Notes:** 不移动位置，只切换动画状态

### 状态切换逻辑

| Option | Description | Selected |
|--------|-------------|----------|
| 定时随机切换 | 基于时间的随机切换（如 5 分钟无操作→sleep），简单可靠 | ✓ |
| 按时段切换 | 根据时间段自动切换（白天→idle，夜晚→sleep） | |

**User's choice:** 定时随机切换
**Notes:** 简单可靠的方案

---

## Claude's Discretion

- 项目结构组织方式（模块划分、文件命名）
- 具体的 PySide6 窗口标志组合
- Sprite 素材的帧数和帧率
- 数据模型的具体字段设计
- 占位素材的生成方式

## Deferred Ideas

None — discussion stayed within phase scope
