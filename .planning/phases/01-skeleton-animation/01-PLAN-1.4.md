---
wave: 2
depends_on:
  - P1.2
  - P1.3
files_modified:
  - main.py
  - data/settings.py
  - pet/window.py
autonomous: true
---

# P1.4 — 位置与设置持久化

## 目标

实现宠物位置和设置的完整持久化：窗口移动时实时保存位置、应用退出时保存最终状态、启动时恢复上次的位置和动画偏好。确保关闭后重新打开，宠物出现在同一位置。

**覆盖需求：** DAT-01, DAT-02

---

## 任务

### 任务 1：实现窗口位置实时保存

<task>
<read_first>
- pet/window.py（当前 PetWindow 实现）
- data/settings.py（Settings dataclass）
</read_first>
<action>
在 `pet/window.py` 的 `PetWindow` 类中添加位置变化检测和保存功能：

1. 添加信号和保存回调：

```python
from PySide6.QtCore import Signal
```

在 `PetWindow` 类中添加：

```python
    # 位置变化信号（外部连接到保存逻辑）
    position_changed = Signal(int, int)

    def moveEvent(self, event):
        """窗口移动时触发位置变化信号。"""
        super().moveEvent(event)
        pos = event.pos()
        self.position_changed.emit(pos.x(), pos.y())
```

2. 确保 `moveEvent` 方法在 `PetWindow` 类中，与 `paintEvent`、`showEvent` 同级。
</action>
<acceptance_criteria>
- `pet/window.py` 包含 `position_changed = Signal(int, int)`
- `pet/window.py` 包含 `def moveEvent(self, event):`
- `pet/window.py` 包含 `self.position_changed.emit(pos.x(), pos.y())`
- `pet/window.py` 包含 `from PySide6.QtCore import Signal`
</acceptance_criteria>
</task>

---

### 任务 2：实现退出时保存状态

<task>
<read_first>
- main.py（当前内容）
- data/settings.py（Settings.save 方法）
- pet/animator.py（SpriteAnimator.current_state）
- pet/window.py（PetWindow.get_position）
</read_first>
<action>
在 `main.py` 中添加退出时保存逻辑。在 `main()` 函数中，`window.show()` 之后、`sys.exit(app.exec())` 之前，添加退出保存连接：

```python
    # 退出时保存最终状态
    def on_about_to_quit():
        pos = window.get_position()
        s = Settings(
            pet_x=pos[0],
            pet_y=pos[1],
            pet_state=animator.current_state.value,
            volume=settings.volume,
            muted=settings.muted,
            auto_start=settings.auto_start,
        )
        s.save()
        print(f"[SmartDesktopPet] 状态已保存: ({pos[0]}, {pos[1]}) {animator.current_state.value}")

    app.aboutToQuit.connect(on_about_to_quit)
```

同时，连接位置变化信号到实时保存：

```python
    # 位置变化时实时保存（节流：每 500ms 最多保存一次）
    from PySide6.QtCore import QTimer as _QTimer
    _save_throttle = _QTimer()
    _save_throttle.setSingleShot(True)
    _save_throttle.setInterval(500)

    def _do_save_position():
        pos = window.get_position()
        s = Settings.load()  # 读取当前设置
        s.pet_x = pos[0]
        s.pet_y = pos[1]
        s.save()

    _save_throttle.timeout.connect(_do_save_position)

    def _on_position_changed(x, y):
        if not _save_throttle.isActive():
            _save_throttle.start()

    window.position_changed.connect(_on_position_changed)
```
</action>
<acceptance_criteria>
- `main.py` 包含 `app.aboutToQuit.connect(on_about_to_quit)`
- `main.py` 包含 `pos = window.get_position()` 在退出回调中
- `main.py` 包含 `animator.current_state.value` 获取状态字符串
- `main.py` 包含 `s.save()` 在退出回调中
- `main.py` 包含 `window.position_changed.connect(_on_position_changed)`
- `main.py` 包含节流逻辑 `_save_throttle`（500ms 间隔）
</acceptance_criteria>
</task>

---

### 任务 3：实现启动时恢复完整状态

<task>
<read_first>
- main.py（当前内容）
- data/settings.py（Settings.load 方法）
- pet/animator.py（SpriteAnimator.set_state）
- pet/states.py（PetState 枚举）
</read_first>
<action>
在 `main.py` 中，在 `animator.load_frames()` 之后、`animator.start()` 之前，添加状态恢复逻辑：

```python
    # 恢复上次的动画状态
    try:
        saved_state = PetState(settings.pet_state)
        animator.set_state(saved_state)
    except (ValueError, KeyError):
        pass  # 无效状态值，保持默认 IDLE
```

需要在文件顶部添加 `PetState` 的导入：

```python
from pet.states import PetState
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.states import PetState`
- `main.py` 包含 `saved_state = PetState(settings.pet_state)`
- `main.py` 包含 `animator.set_state(saved_state)`
- `main.py` 包含 `except (ValueError, KeyError):` 异常处理
- 状态恢复代码位于 `animator.load_frames()` 之后、`animator.start()` 之前
</acceptance_criteria>
</task>

---

### 任务 4：验证完整持久化流程

<task>
<read_first>
- main.py（最终版本）
- pet/window.py（包含 position_changed 信号）
- data/settings.py（Settings 类）
</read_first>
<action>
无需代码修改。通过以下验证步骤确认持久化流程完整：

1. 启动应用 `python main.py`
2. 确认 `%APPDATA%/SmartDesktopPet/settings.json` 文件已创建
3. 确认文件包含 `_schema_version: 1`
4. 确认文件包含 `pet.x`、`pet.y` 坐标
5. 关闭应用
6. 重新启动，确认宠物出现在上次关闭时的位置
7. 在 `%APPDATA%/SmartDesktopPet/settings.json` 中手动修改 `pet.x` 和 `pet.y` 为不同值
8. 重新启动，确认宠物出现在新坐标

运行以下验证脚本：
```python
import json
import os
from pathlib import Path

settings_path = Path(os.environ.get("APPDATA", "~")) / "SmartDesktopPet" / "settings.json"
assert settings_path.exists(), f"settings.json not found at {settings_path}"

with open(settings_path, "r", encoding="utf-8") as f:
    data = json.load(f)

assert "_schema_version" in data, "Missing _schema_version"
assert data["_schema_version"] == 1, f"Wrong schema version: {data['_schema_version']}"
assert "pet" in data, "Missing pet section"
assert "x" in data["pet"], "Missing pet.x"
assert "y" in data["pet"], "Missing pet.y"
assert "state" in data["pet"], "Missing pet.state"
assert "preferences" in data, "Missing preferences section"
print("Persistence verification OK")
```
</action>
<acceptance_criteria>
- `%APPDATA%/SmartDesktopPet/settings.json` 文件存在
- 文件可被 `json.load()` 正常解析
- 文件包含 `"_schema_version": 1`
- 文件包含 `"pet": {"x": ..., "y": ..., "state": ...}`
- 文件包含 `"preferences": {"volume": ..., "muted": ..., "auto_start": ...}`
- 验证脚本输出 "Persistence verification OK"
</acceptance_criteria>
</task>

---

## 验证

1. **实时保存验证：** 启动应用，拖动窗口（Phase 2 前可手动用代码移动），检查 `settings.json` 中的坐标是否更新
2. **退出保存验证：** 启动应用 → 关闭 → 检查 `settings.json` 中坐标是否为关闭前的最终位置
3. **位置恢复验证：**
   - 启动应用，记下宠物位置
   - 关闭应用
   - 重新启动，确认宠物在同一位置
4. **状态恢复验证：**
   - 启动应用，等待状态切换到 WALK 或 SLEEP
   - 关闭应用，检查 `settings.json` 中 `pet.state` 是否为当前状态
   - 重新启动，确认宠物从上次的状态继续
5. **损坏数据恢复验证：**
   - 将 `settings.json` 内容改为 `{"pet": {"x": "invalid"}}`
   - 启动应用，确认不崩溃，使用默认值
6. **文件格式验证：** 确认 `settings.json` 使用 UTF-8 编码、2 空格缩进、`ensure_ascii=False`（中文可正常显示）

---

## must_haves

- `PetWindow.position_changed` 信号在 `moveEvent` 中触发
- 位置保存使用 500ms 节流，避免频繁写入磁盘
- `app.aboutToQuit` 信号连接到退出保存回调
- 退出保存包含完整状态：位置 (x, y)、动画状态、所有偏好设置
- 启动恢复使用 `try/except` 处理无效状态值
- `Settings.load()` 在文件不存在或格式错误时不崩溃
- 所有 JSON 写入使用 `encoding="utf-8"` 和 `ensure_ascii=False`
- `settings.json` 包含 `_schema_version: 1`
