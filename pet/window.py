"""全屏透明宠物窗口 — 水獭直接浮在桌面上"""
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import QWidget, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint, QSize, QRect, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtGui import QPainter, QPixmap, QAction


class PetWindow(QWidget):
    """全屏透明、始终置顶的宠物窗口。

    窗口覆盖整个屏幕且完全透明，用户只看到水獭"浮"在桌面上。
    精灵在窗口内通过 (_sprite_x, _sprite_y) 定位。

    窗口标志组合：
    - FramelessWindowHint: 无标题栏、无边框
    - WindowStaysOnTopHint: 始终置顶
    - Tool: 不在任务栏和 Alt+Tab 中显示

    属性：
    - WA_TranslucentBackground: 真正的 per-pixel alpha 透明
    """

    # 精灵画布基准尺寸（180x180）
    BASE_CANVAS = 180

    # 精灵位置变化信号（外部连接到保存逻辑）
    position_changed = Signal(int, int)
    # 点击信号（非拖拽时触发）
    clicked = Signal()
    # 菜单动作信号（Phase 3+ 连接）
    schedule_requested = Signal()
    chat_requested = Signal()
    settings_requested = Signal()
    # 调试：手动切换状态信号
    debug_state_requested = Signal(str)
    # 大小变化信号
    scale_changed = Signal(float)
    # 换装开关信号
    costume_toggle = Signal(bool)
    # 手动试穿服装信号 (costume_id, 空字符串表示脱下)
    costume_try = Signal(str)

    def __init__(self, scale: float = 1.0, parent=None):
        super().__init__(parent)

        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 启用透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # 允许接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 换装开关状态
        self._costume_enabled = True

        # 精灵缩放倍数
        self._scale = scale

        # 精灵在窗口内的坐标（屏幕坐标）
        self._sprite_x: int = 200
        self._sprite_y: int = 200

        # 当前要渲染的 QPixmap
        self._current_pixmap: QPixmap | None = None

        # 服装偏移（精灵在扩展画布中的偏移，用于居中显示）
        self._costume_offset_x: int = 0
        self._costume_offset_y: int = 0

        # 拖拽相关
        self._dragging = False
        self._drag_start_pos: QPoint | None = None
        self._sprite_start_pos: tuple[int, int] | None = None
        self._drag_threshold = 5
        self._click_on_sprite = False  # 点击是否在精灵范围内

    def showEvent(self, event):
        """在窗口显示后设置全屏大小。"""
        super().showEvent(event)
        # 全屏覆盖
        screen = self.screen()
        if screen:
            self.setGeometry(screen.geometry())
        self.setFocus()

    def set_pixmap(self, pixmap: QPixmap, costume_offset_x: int = 0, costume_offset_y: int = 0) -> None:
        """设置当前要渲染的精灵帧。"""
        self._current_pixmap = pixmap
        self._costume_offset_x = costume_offset_x
        self._costume_offset_y = costume_offset_y
        self.update()  # 触发 paintEvent 重绘

    def _get_sprite_rect(self) -> QRect:
        """获取精灵在窗口内的绘制区域（考虑缩放）。"""
        if not self._current_pixmap or self._current_pixmap.isNull():
            return QRect(self._sprite_x, self._sprite_y, 0, 0)
        w = int(self.BASE_CANVAS * 1.4 * self._scale)
        h = w  # 正方形
        return QRect(self._sprite_x, self._sprite_y, w, h)

    def _is_point_on_sprite(self, point: QPoint) -> bool:
        """判断点是否在精灵范围内。"""
        return self._get_sprite_rect().contains(point)

    def paintEvent(self, event):
        """在精灵位置绘制当前帧。"""
        painter = QPainter(self)
        # 清除背景为全透明
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        if self._current_pixmap and not self._current_pixmap.isNull():
            # 计算精灵显示尺寸
            sprite_w = int(self.BASE_CANVAS * 1.4 * self._scale)
            sprite_h = sprite_w
            # 缩放精灵（保持像素风锐利）
            scaled = self._current_pixmap.scaled(
                QSize(sprite_w, sprite_h),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            # 服装偏移也需要缩放
            pixmap_w = self._current_pixmap.width()
            pixmap_h = self._current_pixmap.height()
            display_scale_x = sprite_w / pixmap_w if pixmap_w else 1.0
            display_scale_y = sprite_h / pixmap_h if pixmap_h else 1.0
            offset_x = int(self._costume_offset_x * display_scale_x)
            offset_y = int(self._costume_offset_y * display_scale_y)
            # 居中绘制，但根据服装偏移调整位置
            # 偏移表示精灵在扩展画布中的位置，需要向上/左偏移使精灵居中
            x = self._sprite_x + (sprite_w - scaled.width()) // 2 - offset_x
            y = self._sprite_y + (sprite_h - scaled.height()) // 2 - offset_y
            painter.drawPixmap(x, y, scaled)

        painter.end()

    def set_sprite_position(self, x: int, y: int) -> None:
        """设置精灵在屏幕上的位置，约束不超出屏幕边界。"""
        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            sprite_size = int(self.BASE_CANVAS * 1.4 * self._scale)
            x = max(geo.left(), min(x, geo.right() - sprite_size))
            y = max(geo.top(), min(y, geo.bottom() - sprite_size))
        self._sprite_x = x
        self._sprite_y = y
        self.position_changed.emit(x, y)
        self.update()

    def get_position(self) -> tuple[int, int]:
        """获取精灵当前屏幕坐标。"""
        return (self._sprite_x, self._sprite_y)

    def set_scale(self, scale: float) -> None:
        """动态调整精灵大小。"""
        self._scale = scale
        # 约束精灵位置（新尺寸可能超出边界）
        self.set_sprite_position(self._sprite_x, self._sprite_y)
        self.scale_changed.emit(scale)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_point_on_sprite(pos):
                self._dragging = True
                self._click_on_sprite = True
                self._drag_start_pos = event.globalPosition().toPoint()
                self._sprite_start_pos = (self._sprite_x, self._sprite_y)
                event.accept()
            else:
                self._click_on_sprite = False
                event.ignore()
        elif event.button() == Qt.MouseButton.RightButton:
            if self._is_point_on_sprite(pos):
                self._click_on_sprite = True
                # 右键菜单由 contextMenuEvent 处理
                super().mousePressEvent(event)
            else:
                self._click_on_sprite = False
                event.ignore()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start_pos and self._sprite_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_x = self._sprite_start_pos[0] + delta.x()
            new_y = self._sprite_start_pos[1] + delta.y()
            self.set_sprite_position(new_x, new_y)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            moved = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

            if moved < self._drag_threshold:
                self.clicked.emit()

            self._dragging = False
            self._drag_start_pos = None
            self._sprite_start_pos = None
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """数字键 1-9 手动切换状态，0 恢复自动（调试用）。"""
        _KEY_STATE_MAP = {
            Qt.Key.Key_1: "idle",
            Qt.Key.Key_2: "walk",
            Qt.Key.Key_3: "sleep",
            Qt.Key.Key_4: "happy",
            Qt.Key.Key_5: "alert",
            Qt.Key.Key_6: "eat",
            Qt.Key.Key_7: "play",
            Qt.Key.Key_8: "groom",
            Qt.Key.Key_9: "rest",
        }
        state = _KEY_STATE_MAP.get(event.key())
        if state:
            self.debug_state_requested.emit(state)
        elif event.key() == Qt.Key.Key_0:
            self.debug_state_requested.emit("__resume__")
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """右键弹出上下文菜单（仅在精灵范围内）。"""
        if not self._click_on_sprite:
            event.ignore()
            return

        menu = QMenu(self)

        schedule_action = QAction("日程", self)
        schedule_action.triggered.connect(self.schedule_requested.emit)

        chat_action = QAction("聊天", self)
        chat_action.triggered.connect(self.chat_requested.emit)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.settings_requested.emit)

        # 换装开关
        costume_action = QAction("节日换装", self)
        costume_action.setCheckable(True)
        costume_action.setChecked(self._costume_enabled)
        costume_action.triggered.connect(lambda checked: self.costume_toggle.emit(checked))

        # 试穿服装子菜单
        try_menu = menu.addMenu("试穿服装")
        costume_names = {
            "red_lantern_hat": "🧧 红灯笼帽 (春节)",
            "moon_cake": "🥮 月饼 (中秋)",
            "dragon_hat": "🐉 龙帽 (端午)",
            "flag_ribbon": "🇨🇳 国旗飘带 (国庆)",
            "party_hat": "🎉 派对帽 (元旦)",
            "balloon": "🎈 气球 (儿童节)",
        }
        for cid, label in costume_names.items():
            action = QAction(label, self)
            action.triggered.connect(lambda checked, c=cid: self.costume_try.emit(c))
            try_menu.addAction(action)
        try_menu.addSeparator()
        clear_action = QAction("脱下服装", self)
        clear_action.triggered.connect(lambda: self.costume_try.emit(""))
        try_menu.addAction(clear_action)

        # 大小子菜单
        size_menu = menu.addMenu("大小")
        size_presets = [
            ("小 (0.7x)", 0.7),
            ("标准 (1.0x)", 1.0),
            ("大 (1.5x)", 1.5),
            ("特大 (2.0x)", 2.0),
        ]
        for label, scale_val in size_presets:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(abs(self._scale - scale_val) < 0.01)
            action.triggered.connect(lambda checked, s=scale_val: self.set_scale(s))
            size_menu.addAction(action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)

        menu.addAction(schedule_action)
        menu.addAction(chat_action)
        menu.addAction(settings_action)
        menu.addAction(costume_action)
        menu.addMenu(size_menu)
        menu.addSeparator()
        menu.addAction(exit_action)

        menu.exec(event.globalPos())

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
