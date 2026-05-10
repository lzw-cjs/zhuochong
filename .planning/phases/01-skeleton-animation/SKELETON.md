# Walking Skeleton — Phase 1 骨架定义

## 什么是 Walking Skeleton？

Walking Skeleton 是系统最薄的纵向切片——它贯穿所有层（UI → 逻辑 → 数据），证明整个技术栈端到端可以工作。不是功能完整的应用，而是一条从头到尾能跑通的路径。

---

## 骨架定义

**一句话描述：** 一个透明窗口中显示一个不断循环动画的树懒占位图，关闭后重新打开，树懒出现在上次的位置。

### 端到端路径

```
用户启动 main.py
    → PySide6 应用创建
    → Settings 从 %APPDATA%/SmartDesktopPet/settings.json 加载（或使用默认值）
    → PetWindow 创建（透明无边框、始终置顶）
    → SpriteAnimator 加载占位素材（代码生成的 32x32 几何树懒）
    → QTimer 驱动帧循环，paintEvent 渲染当前帧
    → 窗口移动时 position_changed 信号触发保存
    → 用户关闭应用
    → app.aboutToQuit 触发最终状态保存到 settings.json
    → 用户重新启动 main.py
    → Settings.load() 读取上次保存的位置
    → PetWindow 出现在上次的位置
```

### 验证标准

骨架完成时，必须满足以下所有条件：

| # | 验证项 | 检测方法 |
|---|--------|----------|
| 1 | 透明窗口出现，无白背景 | 手动观察：窗口背景完全透明，可见桌面 |
| 2 | 窗口无边框、无标题栏 | 手动观察：无标准窗口装饰 |
| 3 | 窗口不在任务栏显示 | 手动观察：任务栏无条目 |
| 4 | 窗口始终在其他窗口之上 | 打开记事本等窗口，宠物窗口仍在最上层 |
| 5 | 树懒动画在循环播放 | 手动观察：占位图帧序列持续循环 |
| 6 | 动画状态自动切换 | 等待 30-90 秒，观察状态从 idle 变为 walk |
| 7 | 关闭后重新打开位置不变 | 启动 → 关闭 → 重新启动，位置一致 |
| 8 | settings.json 包含完整数据 | 检查文件包含 `_schema_version`、`pet`、`preferences` |
| 9 | Win11 无闪烁 | 手动观察：窗口渲染稳定，无抖动 |

### 不属于骨架的功能

以下功能不在骨架范围内，将在后续计划中实现：

- 拖拽移动宠物（P2.1）
- 点击触发动画反馈（P2.2）
- 右键菜单（P2.3）
- 系统托盘（P2.4）
- 聊天系统（Phase 3）
- 日程管理（Phase 4）
- 提醒引擎（Phase 5）
- 正式像素画素材（替换占位素材）
- 打包为 .exe（Phase 6）

---

## 实现路径

骨架由以下 4 个计划按序实现：

| 顺序 | 计划 | 波次 | 骨架贡献 |
|------|------|------|----------|
| 1 | P1.1 项目骨架与数据层 | Wave 0 | JsonStore 读写 + Settings + main.py 入口 |
| 2 | P1.2 透明宠物窗口 | Wave 1 | PetWindow 透明无边框 + 智能置顶 |
| 3 | P1.3 Sprite 动画引擎 | Wave 1 | 状态枚举 + 帧动画 + 占位素材 + 行为调度 |
| 4 | P1.4 位置与设置持久化 | Wave 2 | 位置保存/恢复 + 退出保存 + 启动恢复 |

### 最小可行骨架（跳过可选功能）

如果需要更快验证骨架，可跳过以下功能：

- **可跳过：** 智能置顶（全屏检测）—— 骨架不依赖此功能
- **可跳过：** BehaviorScheduler 随机切换 —— 可先用固定 idle 循环验证动画引擎
- **可跳过：** 位置实时保存节流 —— 可先只做退出时保存

---

## 骨架验收清单

骨架完成后，运行以下命令验证：

```bash
# 1. 模块导入验证
python -c "from pet.window import PetWindow; from pet.animator import SpriteAnimator; from pet.behavior import BehaviorScheduler; from data.settings import Settings; print('All modules OK')"

# 2. 启动应用
python main.py

# 3. 检查数据文件
python -c "
import json, os
from pathlib import Path
p = Path(os.environ['APPDATA']) / 'SmartDesktopPet' / 'settings.json'
data = json.load(open(p, encoding='utf-8'))
assert data['_schema_version'] == 1
assert 'pet' in data and 'x' in data['pet']
print('Data file OK')
"

# 4. 位置恢复验证
python -c "
import json, os
from pathlib import Path
p = Path(os.environ['APPDATA']) / 'SmartDesktopPet' / 'settings.json'
data = json.load(open(p, encoding='utf-8'))
print(f'Last position: ({data[\"pet\"][\"x\"]}, {data[\"pet\"][\"y\"]})')
print(f'Last state: {data[\"pet\"][\"state\"]}')
"
```

全部通过 → 骨架完成，可进入 Phase 2。

---

*Walking Skeleton 定义: Phase 1*
*创建时间: 2026-05-09*
