---
wave: 0
depends_on: []
files_modified:
  - pet/window.py
  - main.py
autonomous: true
---

# P2.1 — Drag-and-Drop

## 目标

实现宠物窗口的鼠标拖拽功能：按下鼠标左键拖动宠物移动，松开后宠物停在新位置并持久化。区分点击和拖拽（5px 阈值），约束窗口不超出屏幕边界。

**覆盖需求：** PET-02

---

## 任务

### 任务 1：在 PetWindow 中实现拖拽逻辑

<task>
<read_first>
- pet/window.py（当前 PetWindow 实现）
- main.py（当前 main 函数）
</read_first>
<action>
在 `pet/window.py` 的 `PetWindow` 类中添加拖拽功能：

1. 添加拖拽相关属性和信号：

```python
    # 拖拽相关
    _dragging = False
    _drag_start_pos = None  # 鼠标按下时的全局坐标
    _window_start_pos = None  # 窗口初始位置
    _drag_threshold = 5  # 区分点击和拖拽的像素阈值

    # 点击信号（非拖拽时触发）
    clicked = Signal()
```

2. 实现 mousePressEvent：

```python
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_pos = self.pos()
            event.accept()
```

3. 实现 mouseMoveEvent：

```python
    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._window_start_pos + delta

            # 约束到屏幕边界
            screen = self.screen()
            if screen:
                geo = screen.availableGeometry()
                new_pos.setX(max(geo.left(), min(new_pos.x(), geo.right() - self.width())))
                new_pos.setY(max(geo.top(), min(new_pos.y(), geo.bottom() - self.height())))

            self.move(new_pos)
            event.accept()
```

4. 实现 mouseReleaseEvent：

```python
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            moved = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

            if moved < self._drag_threshold:
                # 移动距离小于阈值，视为点击
                self.clicked.emit()

            self._dragging = False
            self._drag_start_pos = None
            self._window_start_pos = None
            event.accept()
```
</action>
<acceptance_criteria>
- `pet/window.py` 包含 `clicked = Signal()`
- `pet/window.py` 包含 `def mousePressEvent(self, event):`
- `pet/window.py` 包含 `def mouseMoveEvent(self, event):`
- `pet/window.py` 包含 `def mouseReleaseEvent(self, event):`
- `pet/window.py` 包含 `_drag_threshold = 5`
- `pet/window.py` 包含 `self._dragging = True` 在 mousePressEvent 中
- `pet/window.py` 包含 `event.globalPosition().toPoint()` 获取全局坐标
- `pet/window.py` 包含 `screen.availableGeometry()` 约束屏幕边界
- `pet/window.py` 包含 `self.clicked.emit()` 在非拖拽释放时触发
- `pet/window.py` 包含距离计算 `moved < self._drag_threshold`
</acceptance_criteria>
</task>

---

### 任务 2：连接 clicked 信号到 main.py

<task>
<read_first>
- main.py（当前内容）
- pet/window.py（包含 clicked 信号）
- pet/behavior.py（BehaviorScheduler.on_user_interaction）
</read_first>
<action>
在 `main.py` 中，在 `behavior.start()` 之后，添加点击信号连接：

```python
    # 点击宠物触发交互反馈
    window.clicked.connect(behavior.on_user_interaction)
```
</action>
<acceptance_criteria>
- `main.py` 包含 `window.clicked.connect(behavior.on_user_interaction)`
- 该代码位于 `behavior.start()` 之后
</acceptance_criteria>
</task>

---

## 验证

1. **拖拽验证：** 运行 `python main.py`，按住左键拖动宠物，确认宠物跟随鼠标移动
2. **屏幕约束验证：** 尝试将宠物拖到屏幕边缘，确认窗口不会超出屏幕
3. **点击验证：** 快速点击（不拖动），确认宠物切换到 happy 状态
4. **位置持久化验证：** 拖动宠物到新位置，关闭并重启，确认宠物出现在新位置

---

## must_haves

- 使用 `event.globalPosition().toPoint()` 获取鼠标全局坐标（PySide6 API）
- 拖拽阈值为 5 像素（`_drag_threshold = 5`）
- 距离计算使用欧几里得距离 `sqrt(dx² + dy²)`
- 屏幕约束使用 `screen.availableGeometry()`
- `clicked` 信号在非拖拽释放时触发
- `position_changed` 信号在 moveEvent 中已存在（Phase 1），拖拽时自动触发
