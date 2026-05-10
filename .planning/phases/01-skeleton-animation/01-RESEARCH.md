# Phase 1: Skeleton & Animation — Research

**Researched:** 2026-05-09
**Status:** Ready for planning

---

## 1. PySide6 透明无边框窗口

**Confidence: HIGH**

### 窗口标志组合

```python
window.setWindowFlags(
    Qt.WindowType.FramelessWindowHint      # 无标题栏、无边框
    | Qt.WindowType.WindowStaysOnTopHint   # 始终置顶
    | Qt.WindowType.Tool                   # 任务栏隐藏 + Alt+Tab 隐藏
)
window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
```

### 关键注意事项

| 问题 | 解决方案 |
|------|----------|
| Win11 RHI 渲染导致透明失效 | 启动时设置 `QSG_RHI_BACKEND=opengl` 环境变量 |
| 高 DPI 缩放 | 使用 `QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` |
| PerMonitorV2 DPI | 在应用入口处设置 DPI awareness |

### 智能置顶实现

```python
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def is_fullscreen_active():
    """检测当前是否有全屏应用"""
    hwnd = user32.GetForegroundWindow()
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    # 获取窗口所在显示器的尺寸
    monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
    # 比较窗口尺寸与显示器尺寸
    # 如果相等则为全屏应用
```

---

## 2. Sprite 帧动画引擎

**Confidence: HIGH**

### 推荐方案：QPixmap + QTimer + paintEvent

```python
class SpriteAnimator:
    def __init__(self):
        self.frames = {}  # state -> list[QPixmap]
        self.current_state = "idle"
        self.current_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_frame)

    def load_state(self, state_name, sprite_sheet, frame_count, frame_width, frame_height):
        """从 sprite sheet 加载帧序列"""
        frames = []
        for i in range(frame_count):
            frame = sprite_sheet.copy(i * frame_width, 0, frame_width, frame_height)
            frames.append(frame)
        self.frames[state_name] = frames

    def set_state(self, state_name):
        if state_name != self.current_state:
            self.current_state = state_name
            self.current_frame = 0

    def advance_frame(self):
        frames = self.frames[self.current_state]
        self.current_frame = (self.current_frame + 1) % len(frames)

    def current_pixmap(self):
        return self.frames[self.current_state][self.current_frame]
```

### 状态机设计（推荐自定义，避免 QStateMachine）

```python
from enum import Enum

class PetState(Enum):
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"

# 转换表：当前状态 -> 允许的目标状态
TRANSITIONS = {
    PetState.IDLE: [PetState.WALK, PetState.SLEEP, PetState.HAPPY],
    PetState.WALK: [PetState.IDLE, PetState.HAPPY],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY],
    PetState.HAPPY: [PetState.IDLE],
}
```

### 帧率建议

| 状态 | 帧数 | 帧间隔 | 说明 |
|------|------|--------|------|
| idle | 4 帧 | 500ms | 慢悠悠挂在树枝上 |
| walk | 6 帧 | 300ms | 缓慢爬行 |
| sleep | 4 帧 | 800ms | 蜷缩呼吸起伏 |
| happy | 4 帧 | 200ms | 开心摇晃 |

---

## 3. 占位素材生成

**Confidence: HIGH**

### 方案：代码生成简单几何占位图

```python
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt

def generate_placeholder_sloth(width=32, height=32):
    """生成 32x32 占位树懒图"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 身体 - 椭圆
    painter.setBrush(QColor(139, 90, 43))  # 棕色
    painter.drawEllipse(8, 10, 16, 18)

    # 眼睛 - 两个小圆
    painter.setBrush(QColor(0, 0, 0))
    painter.drawEllipse(12, 14, 3, 3)
    painter.drawEllipse(19, 14, 3, 3)

    # 爪子 - 线条
    painter.setPen(QPen(QColor(139, 90, 43), 2))
    painter.drawLine(8, 20, 4, 24)
    painter.drawLine(24, 20, 28, 24)

    painter.end()
    return pixmap
```

每个动画状态生成略有不同的占位图（如 sleep 闭眼，happy 嘴巴张开），确保动画循环正常工作。

---

## 4. JSON 原子写入

**Confidence: HIGH**

### 实现方案

```python
import json
import os
import tempfile
from pathlib import Path

APPDATA_DIR = Path(os.environ.get("APPDATA", "~")) / "SmartDesktopPet"

class JsonStore:
    def __init__(self, filename):
        self.filepath = APPDATA_DIR / filename
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def load(self, default=None):
        if not self.filepath.exists():
            return default or {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        # 原子写入：先写临时文件，再 os.replace
        fd, tmp_path = tempfile.mkstemp(
            dir=self.filepath.parent,
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except:
            os.unlink(tmp_path)
            raise
```

### 数据结构设计

```python
# settings.json
{
    "_schema_version": 1,
    "pet": {
        "x": 100,
        "y": 200,
        "state": "idle"
    },
    "preferences": {
        "volume": 50,
        "muted": False,
        "auto_start": False
    },
    "calendar": {
        "default_color": "#4CAF50",
        "priority_labels": ["低", "中", "高"]
    }
}
```

---

## 5. 定时状态切换

**Confidence: HIGH**

### 实现方案

```python
import random
from PySide6.QtCore import QTimer

class BehaviorScheduler:
    """定时随机切换动画状态"""

    # 无操作后切换到 sleep 的超时时间 (ms)
    IDLE_TIMEOUT = 5 * 60 * 1000  # 5 分钟
    # 状态切换后回到 idle 的时间 (ms)
    RETURN_TIMEOUT = 10 * 1000  # 10 秒

    def __init__(self, animator):
        self.animator = animator
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.on_idle_timeout)
        self.idle_timer.setSingleShot(True)

        self.return_timer = QTimer()
        self.return_timer.timeout.connect(self.on_return_timeout)
        self.return_timer.setSingleShot(True)

    def on_user_interaction(self):
        """用户交互时调用"""
        self.idle_timer.stop()
        self.return_timer.stop()
        self.animator.set_state(PetState.HAPPY)
        self.return_timer.start(self.RETURN_TIMEOUT)

    def on_idle_timeout(self):
        """无操作超时，切换到 sleep"""
        self.animator.set_state(PetState.SLEEP)

    def on_return_timeout(self):
        """状态恢复到 idle"""
        self.animator.set_state(PetState.IDLE)
        self.idle_timer.start(self.IDLE_TIMEOUT)

    def start(self):
        self.idle_timer.start(self.IDLE_TIMEOUT)
```

---

## 6. 项目结构建议

```
smart-desktop-pet/
├── main.py                    # 应用入口
├── pet/
│   ├── __init__.py
│   ├── window.py              # PetWindow (透明无边框窗口)
│   ├── animator.py            # SpriteAnimator + AnimationController
│   ├── behavior.py            # BehaviorScheduler
│   └── states.py              # PetState enum + transitions
├── data/
│   ├── __init__.py
│   ├── store.py               # JsonStore 原子读写
│   └── settings.py            # Settings dataclass
├── assets/
│   ├── sprites/               # 占位素材目录
│   │   ├── idle/              # idle 帧序列
│   │   ├── walk/
│   │   ├── sleep/
│   │   └── happy/
│   └── sounds/                # 音效 (后续阶段)
├── requirements.txt
└── .planning/
```

---

## 7. 关键 Pitfall 总结

| Pitfall | 影响 | 解决方案 |
|---------|------|----------|
| Win11 RHI 渲染 | 透明窗口失效，出现黑/白背景 | `QSG_RHI_BACKEND=opengl` |
| 高 DPI 缩放 | 宠物位置偏移、素材模糊 | `PassThrough` + PerMonitorV2 |
| QTimer 累积误差 | 动画帧率不稳定 | 使用 `QTimer.singleShot` 或校正逻辑 |
| JSON 并发写入 | 数据损坏 | 原子写入 + filelock（Phase 1 可简化） |
| PyInstaller 路径 | 打包后资源找不到 | `get_asset_path()` 兼容 dev/prod（Phase 6） |

---

*Phase: 1-Skeleton & Animation*
*Research completed: 2026-05-09*
