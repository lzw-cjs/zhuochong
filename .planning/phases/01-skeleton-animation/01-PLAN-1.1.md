---
wave: 0
depends_on: []
files_modified:
  - main.py
  - requirements.txt
  - data/__init__.py
  - data/store.py
  - data/settings.py
  - pet/__init__.py
autonomous: true
---

# P1.1 — 项目骨架与数据层

## 目标

搭建项目目录结构，安装 PySide6 依赖，实现 JsonStore 原子读写、Settings dataclass、以及 main.py 入口文件。本计划是整个项目的地基，后续所有计划都依赖于此。

**覆盖需求：** DAT-01, DAT-02

---

## 任务

### 任务 1：创建项目目录结构

<task>
<read_first>
- CLAUDE.md（项目结构约定）
</read_first>
<action>
在项目根目录 `C:\Users\李打爷的电脑\Desktop\zhuochong\` 下创建以下目录结构：

```
main.py                    (空文件，后续填充)
requirements.txt           (空文件，后续填充)
pet/
    __init__.py            (空文件)
data/
    __init__.py            (空文件)
assets/
    sprites/
        idle/              (空目录)
        walk/              (空目录)
        sleep/             (空目录)
        happy/             (空目录)
    sounds/                (空目录)
```

每个 `__init__.py` 文件内容为空。
</action>
<acceptance_criteria>
- `main.py` 文件存在
- `requirements.txt` 文件存在
- `pet/__init__.py` 文件存在
- `data/__init__.py` 文件存在
- `assets/sprites/idle/` 目录存在
- `assets/sprites/walk/` 目录存在
- `assets/sprites/sleep/` 目录存在
- `assets/sprites/happy/` 目录存在
- `assets/sounds/` 目录存在
</acceptance_criteria>
</task>

---

### 任务 2：创建 requirements.txt

<task>
<read_first>
- requirements.txt（当前内容）
- CLAUDE.md（依赖版本矩阵）
</read_first>
<action>
将 `requirements.txt` 写入以下内容：

```
PySide6>=6.8.0
```

Phase 1 仅需 PySide6 核心依赖。`icalendar`、`recurring-ical-events`、`filelock` 等在后续阶段添加。
</action>
<acceptance_criteria>
- `requirements.txt` 包含文本 `PySide6>=6.8.0`
- 文件不包含 `icalendar`、`filelock`、`pygame` 等非本阶段依赖
</acceptance_criteria>
</task>

---

### 任务 3：实现 JsonStore 原子读写

<task>
<read_first>
- data/__init__.py（当前内容）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（JSON 原子写入参考实现，第 4 节）
</read_first>
<action>
在 `data/store.py` 中实现 `JsonStore` 类：

```python
"""JSON 原子读写存储"""
import json
import os
import tempfile
from pathlib import Path

APPDATA_DIR = Path(os.environ.get("APPDATA", "~")) / "SmartDesktopPet"


class JsonStore:
    """JSON 文件的原子读写封装。

    使用 write-to-temp + os.replace 模式确保写入过程中断电或崩溃不会损坏数据。
    """

    def __init__(self, filename: str):
        self.filepath = APPDATA_DIR / filename
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def load(self, default: dict | None = None) -> dict:
        """读取 JSON 文件。文件不存在时返回 default。"""
        if not self.filepath.exists():
            return default if default is not None else {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict) -> None:
        """原子写入 JSON 文件。

        先写入临时文件，再用 os.replace 原子替换目标文件。
        """
        fd, tmp_path = tempfile.mkstemp(
            dir=self.filepath.parent,
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception:
            # 写入失败时清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
```

同时更新 `data/__init__.py`：

```python
from data.store import JsonStore

__all__ = ["JsonStore"]
```
</action>
<acceptance_criteria>
- `data/store.py` 包含 `class JsonStore:`
- `data/store.py` 包含 `APPDATA_DIR = Path(os.environ.get("APPDATA", "~")) / "SmartDesktopPet"`
- `data/store.py` 包含 `def load(self, default: dict | None = None) -> dict:`
- `data/store.py` 包含 `def save(self, data: dict) -> None:`
- `data/store.py` 包含 `os.replace(tmp_path, self.filepath)`
- `data/store.py` 包含 `tempfile.mkstemp`
- `data/store.py` 包含 `encoding="utf-8"`
- `data/store.py` 包含 `ensure_ascii=False`
- `data/__init__.py` 包含 `from data.store import JsonStore`
</acceptance_criteria>
</task>

---

### 任务 4：实现 Settings dataclass

<task>
<read_first>
- data/__init__.py（当前内容）
- data/store.py（刚实现的 JsonStore）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（数据结构设计，第 4 节）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-11 持久化内容，D-13 schema version）
</read_first>
<action>
在 `data/settings.py` 中实现 `Settings` 类：

```python
"""应用设置的读写与持久化"""
from dataclasses import dataclass, field, asdict
from data.store import JsonStore

SCHEMA_VERSION = 1

DEFAULT_SETTINGS = {
    "_schema_version": SCHEMA_VERSION,
    "pet": {
        "x": 200,
        "y": 200,
        "state": "idle"
    },
    "preferences": {
        "volume": 50,
        "muted": False,
        "auto_start": False
    }
}


@dataclass
class Settings:
    """应用设置数据模型。

    字段说明：
        pet_x / pet_y: 宠物在屏幕上的像素坐标
        pet_state: 当前动画状态（idle/walk/sleep/happy）
        volume: 音量 0-100
        muted: 是否静音
        auto_start: 是否开机自启
    """
    pet_x: int = 200
    pet_y: int = 200
    pet_state: str = "idle"
    volume: int = 50
    muted: bool = False
    auto_start: bool = False

    def save(self) -> None:
        """将设置保存到 JSON 文件。"""
        store = JsonStore("settings.json")
        data = {
            "_schema_version": SCHEMA_VERSION,
            "pet": {
                "x": self.pet_x,
                "y": self.pet_y,
                "state": self.pet_state
            },
            "preferences": {
                "volume": self.volume,
                "muted": self.muted,
                "auto_start": self.auto_start
            }
        }
        store.save(data)

    @classmethod
    def load(cls) -> "Settings":
        """从 JSON 文件加载设置。文件不存在或格式错误时返回默认值。"""
        store = JsonStore("settings.json")
        data = store.load(default=DEFAULT_SETTINGS)

        try:
            pet = data.get("pet", {})
            prefs = data.get("preferences", {})
            return cls(
                pet_x=pet.get("x", 200),
                pet_y=pet.get("y", 200),
                pet_state=pet.get("state", "idle"),
                volume=prefs.get("volume", 50),
                muted=prefs.get("muted", False),
                auto_start=prefs.get("auto_start", False),
            )
        except (KeyError, TypeError, ValueError):
            return cls()
```

同时更新 `data/__init__.py`：

```python
from data.store import JsonStore
from data.settings import Settings

__all__ = ["JsonStore", "Settings"]
```
</action>
<acceptance_criteria>
- `data/settings.py` 包含 `SCHEMA_VERSION = 1`
- `data/settings.py` 包含 `@dataclass`
- `data/settings.py` 包含 `class Settings:`
- `data/settings.py` 包含字段：`pet_x: int`, `pet_y: int`, `pet_state: str`, `volume: int`, `muted: bool`, `auto_start: bool`
- `data/settings.py` 包含 `def save(self) -> None:`
- `data/settings.py` 包含 `@classmethod` 和 `def load(cls) -> "Settings":`
- `data/settings.py` 包含 `"_schema_version": SCHEMA_VERSION`
- `data/settings.py` 包含 `JsonStore("settings.json")`
- `data/__init__.py` 包含 `from data.settings import Settings`
</acceptance_criteria>
</task>

---

### 任务 5：创建 main.py 入口文件

<task>
<read_first>
- main.py（当前内容）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（PySide6 窗口标志，第 1 节）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-09 RHI 渲染，D-06 Qt.Tool）
</read_first>
<action>
在 `main.py` 中实现应用入口：

```python
"""Smart Desktop Pet — 应用入口"""
import os
import sys

# Win11 RHI 渲染修复：强制使用 OpenGL 后端
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from data.settings import Settings


def main():
    # DPI 感知设置：避免高 DPI 下宠物位置偏移
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 加载设置
    settings = Settings.load()

    # TODO: Phase 1.2 创建 PetWindow
    # TODO: Phase 1.3 创建 SpriteAnimator
    # TODO: Phase 1.4 持久化连接

    print(f"[SmartDesktopPet] 启动完成")
    print(f"  位置: ({settings.pet_x}, {settings.pet_y})")
    print(f"  状态: {settings.pet_state}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```
</action>
<acceptance_criteria>
- `main.py` 包含 `os.environ["QSG_RHI_BACKEND"] = "opengl"`
- `main.py` 包含 `QApplication.setHighDpiScaleFactorRoundingPolicy`
- `main.py` 包含 `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough`
- `main.py` 包含 `from data.settings import Settings`
- `main.py` 包含 `settings = Settings.load()`
- `main.py` 包含 `if __name__ == "__main__":`
- `main.py` 包含 `app = QApplication(sys.argv)`
- `main.py` 包含 `sys.exit(app.exec())`
</acceptance_criteria>
</task>

---

## 验证

1. **目录结构验证：** 运行 `python -c "from data.store import JsonStore; from data.settings import Settings; print('OK')"` 确认模块可导入
2. **JsonStore 验证：** 运行以下测试脚本确认原子写入正常：
   ```python
   from data.store import JsonStore
   store = JsonStore("_test.json")
   store.save({"test": "value"})
   loaded = store.load()
   assert loaded["test"] == "value", f"Expected 'value', got {loaded}"
   import os; os.unlink(store.filepath)
   print("JsonStore OK")
   ```
3. **Settings 验证：** 运行以下测试脚本确认设置读写正常：
   ```python
   from data.settings import Settings
   s = Settings(pet_x=100, pet_y=300)
   s.save()
   s2 = Settings.load()
   assert s2.pet_x == 100 and s2.pet_y == 300, f"Mismatch: {s2}"
   print("Settings OK")
   ```
4. **main.py 验证：** 运行 `python main.py` 确认启动无报错（窗口将在后续计划中创建）

---

## must_haves

- JsonStore 使用 `os.replace()` 实现原子写入（不能用 `os.rename()`，Windows 上不原子）
- JsonStore 使用 `tempfile.mkstemp()` 创建临时文件
- Settings JSON 包含 `_schema_version` 字段
- Settings.load() 在文件不存在时返回默认值，不抛异常
- main.py 在 QApplication 创建前设置 `QSG_RHI_BACKEND=opengl`
- main.py 设置 DPI 缩放策略为 PassThrough
- 所有文件使用 `encoding="utf-8"` 和 `ensure_ascii=False`
