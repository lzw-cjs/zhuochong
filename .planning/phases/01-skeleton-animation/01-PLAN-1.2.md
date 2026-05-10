---
wave: 1
depends_on:
  - P1.1
files_modified:
  - pet/window.py
  - pet/__init__.py
  - main.py
autonomous: true
---

# P1.2 — 透明宠物窗口

## 目标

实现 PetWindow：一个透明无边框、始终置顶、不在任务栏显示的 PySide6 窗口，用于承载宠物精灵渲染。窗口在 Windows 11 上无白背景、无闪烁、无任务栏条目。

**覆盖需求：** PET-01

---

## 任务

### 任务 1：实现 PetWindow 基础窗口

<task>
<read_first>
- pet/__init__.py（当前内容）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 1 节：PySide6 透明无边框窗口参考实现）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-06 Qt.Tool 标志，D-07 智能置顶）
</read_first>
<action>
在 `pet/window.py` 中实现 `PetWindow` 类：

```python
"""透明无边框宠物窗口"""
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QPainter, QPixmap


class PetWindow(QWidget):
    """透明无边框、始终置顶的宠物窗口。

    窗口标志组合：
    - FramelessWindowHint: 无标题栏、无边框
    - WindowStaysOnTopHint: 始终置顶
    - Tool: 不在任务栏和 Alt+Tab 中显示

    属性：
    - WA_TranslucentBackground: 真正的 per-pixel alpha 透明
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 启用透明背景（在 show() 之后设置，避免 Win11 RHI 问题）
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # 窗口尺寸固定为 32x32（Sprite 原始尺寸）
        self.setFixedSize(QSize(32, 32))

        # 当前要渲染的 QPixmap
        self._current_pixmap: QPixmap | None = None

    def showEvent(self, event):
        """在窗口显示后设置透明背景属性，避免 Win11 RHI 渲染问题。"""
        super().showEvent(event)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """设置当前要渲染的精灵帧。"""
        self._current_pixmap = pixmap
        self.update()  # 触发 paintEvent 重绘

    def paintEvent(self, event):
        """绘制当前精灵帧。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        if self._current_pixmap and not self._current_pixmap.isNull():
            # 居中绘制精灵
            x = (self.width() - self._current_pixmap.width()) // 2
            y = (self.height() - self._current_pixmap.height()) // 2
            painter.drawPixmap(x, y, self._current_pixmap)

        painter.end()

    def move_to(self, x: int, y: int) -> None:
        """移动窗口到指定屏幕坐标。"""
        self.move(QPoint(x, y))

    def get_position(self) -> tuple[int, int]:
        """获取窗口当前屏幕坐标。"""
        pos = self.pos()
        return (pos.x(), pos.y())
```

更新 `pet/__init__.py`：

```python
from pet.window import PetWindow

__all__ = ["PetWindow"]
```
</action>
<acceptance_criteria>
- `pet/window.py` 包含 `class PetWindow(QWidget):`
- `pet/window.py` 包含 `Qt.WindowType.FramelessWindowHint`
- `pet/window.py` 包含 `Qt.WindowType.WindowStaysOnTopHint`
- `pet/window.py` 包含 `Qt.WindowType.Tool`
- `pet/window.py` 包含 `Qt.WidgetAttribute.WA_TranslucentBackground`
- `pet/window.py` 包含 `Qt.WidgetAttribute.WA_NoSystemBackground`
- `pet/window.py` 包含 `def set_pixmap(self, pixmap: QPixmap) -> None:`
- `pet/window.py` 包含 `def paintEvent(self, event):`
- `pet/window.py` 包含 `def showEvent(self, event):`
- `pet/window.py` 包含 `self.setFixedSize(QSize(32, 32))`
- `pet/__init__.py` 包含 `from pet.window import PetWindow`
</acceptance_criteria>
</task>

---

### 任务 2：集成 PetWindow 到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/window.py（刚实现的 PetWindow）
- data/settings.py（Settings dataclass）
</read_first>
<action>
更新 `main.py`，集成 PetWindow 并从设置恢复位置：

```python
"""Smart Desktop Pet — 应用入口"""
import os
import sys

# Win11 RHI 渲染修复：强制使用 OpenGL 后端
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from data.settings import Settings
from pet.window import PetWindow


def main():
    # DPI 感知设置：避免高 DPI 下宠物位置偏移
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 加载设置
    settings = Settings.load()

    # 创建宠物窗口
    window = PetWindow()
    window.move_to(settings.pet_x, settings.pet_y)
    window.show()

    print(f"[SmartDesktopPet] 启动完成")
    print(f"  位置: ({settings.pet_x}, {settings.pet_y})")
    print(f"  状态: {settings.pet_state}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.window import PetWindow`
- `main.py` 包含 `window = PetWindow()`
- `main.py` 包含 `window.move_to(settings.pet_x, settings.pet_y)`
- `main.py` 包含 `window.show()`
</acceptance_criteria>
</task>

---

### 任务 3：智能置顶（全屏时隐藏）

<task>
<read_first>
- pet/window.py（当前内容）
- .planning/phases/01-skeleton-animation/01-RESEARCH.md（第 1 节：智能置顶实现）
- .planning/phases/01-skeleton-animation/01-CONTEXT.md（D-07 智能置顶）
</read_first>
<action>
在 `pet/window.py` 中添加全屏检测和智能置顶功能。在 `PetWindow` 类中添加以下方法：

```python
    def _is_fullscreen_active(self) -> bool:
        """检测当前前台窗口是否为全屏应用。

        使用 Win32 API 获取前台窗口尺寸，与所在显示器尺寸比较。
        如果窗口覆盖整个显示器，认为是全屏应用。
        """
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == int(self.winId()):
                return False  # 宠物自身窗口不算全屏

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            window_width = rect.right - rect.left
            window_height = rect.bottom - rect.top

            # 获取窗口所在显示器
            monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST

            # 获取显示器信息
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(monitor, ctypes.byref(mi))

            monitor_width = mi.rcMonitor.right - mi.rcMonitor.left
            monitor_height = mi.rcMonitor.bottom - mi.rcMonitor.top

            # 允许 2px 容差（部分应用的全屏窗口可能有微小边框）
            return (
                abs(window_width - monitor_width) <= 2
                and abs(window_height - monitor_height) <= 2
            )
        except Exception:
            return False

    def check_smart_topmost(self) -> None:
        """智能置顶：全屏应用运行时隐藏宠物，否则显示。"""
        if self._is_fullscreen_active():
            if self.isVisible():
                self.hide()
        else:
            if not self.isVisible():
                self.show()
```

同时在文件顶部确认已导入 `ctypes` 和 `wintypes`（任务 1 已导入）。
</action>
<acceptance_criteria>
- `pet/window.py` 包含 `def _is_fullscreen_active(self) -> bool:`
- `pet/window.py` 包含 `def check_smart_topmost(self) -> None:`
- `pet/window.py` 包含 `user32.GetForegroundWindow()`
- `pet/window.py` 包含 `user32.MonitorFromWindow`
- `pet/window.py` 包含 `user32.GetWindowRect`
- `pet/window.py` 包含 `user32.GetMonitorInfoW`
- `pet/window.py` 包含 `abs(window_width - monitor_width) <= 2`
</acceptance_criteria>
</task>

---

### 任务 4：添加智能置顶定时器到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/window.py（包含 check_smart_topmost 方法）
</read_first>
<action>
更新 `main.py`，添加一个 QTimer 定期调用智能置顶检测：

在文件顶部的 import 区域添加：
```python
from PySide6.QtCore import QTimer
```

在 `window.show()` 之后、`sys.exit(app.exec())` 之前添加：
```python
    # 智能置顶检测：每 2 秒检查是否有全屏应用
    topmost_timer = QTimer()
    topmost_timer.timeout.connect(window.check_smart_topmost)
    topmost_timer.start(2000)
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from PySide6.QtCore import QTimer`
- `main.py` 包含 `topmost_timer = QTimer()`
- `main.py` 包含 `topmost_timer.timeout.connect(window.check_smart_topmost)`
- `main.py` 包含 `topmost_timer.start(2000)`
</acceptance_criteria>
</task>

---

## 验证

1. **窗口创建验证：** 运行 `python main.py`，确认：
   - 一个 32x32 的透明窗口出现在屏幕坐标 (settings.pet_x, settings.pet_y) 处
   - 窗口无标题栏、无边框
   - 窗口不出现在 Windows 任务栏中
   - 窗口始终在其他窗口之上
   - 窗口背景完全透明（可以看到桌面壁纸）
2. **位置恢复验证：** 关闭应用后修改 `settings.json` 中的 `pet.x` 和 `pet.y`，重新启动确认窗口出现在新位置
3. **智能置顶验证（可选手动测试）：** 启动一个全屏游戏或视频，确认宠物窗口自动隐藏；退出全屏后宠物重新出现

---

## must_haves

- PetWindow 使用 `FramelessWindowHint | WindowStaysOnTopHint | Tool` 三个窗口标志
- `WA_TranslucentBackground` 在 `showEvent()` 中设置，不能在构造函数中设置（Win11 RHI 兼容性）
- `WA_NoSystemBackground` 在构造函数中设置
- 窗口固定尺寸 32x32
- `paintEvent` 使用 `QPainter` 绘制，关闭 `SmoothPixmapTransform`（像素风保持锐利）
- 全屏检测使用 `GetWindowRect` + `MonitorFromWindow` + `GetMonitorInfoW` 组合
- 全屏检测容差为 2 像素
- 智能置顶检测间隔为 2000ms
